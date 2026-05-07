"""POST /api/v1/uploads — direct multipart upload (dev) or presigned S3 (prod)."""
from __future__ import annotations

import logging
import os
import shutil
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status

from app.api.dependencies import CurrentUser, DBDep
from app.config import get_settings
from app.db.models import LogFile
from app.schemas.upload import LogFileRead, PresignedUploadResponse, DirectUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

PRESIGN_EXPIRES = 900  # 15 dakika
LOCAL_UPLOAD_DIR = Path("/tmp/loglens_uploads")


def _s3_configured() -> bool:
    return bool(settings.aws_access_key_id and settings.aws_secret_access_key)


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


# ── Presigned S3 URL (production) ────────────────────────────────────────────

@router.post("", response_model=PresignedUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    filename: str = Query(..., min_length=1, max_length=512),
    size_bytes: int = Query(..., gt=0, le=settings.max_upload_size_bytes),
    db: DBDep = ...,
    current_user: CurrentUser = ...,
) -> PresignedUploadResponse:
    """Presigned S3 PUT URL oluşturur (AWS credentials gerektirir)."""
    if not _s3_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AWS credentials yapılandırılmamış. /uploads/direct endpoint'ini kullanın.",
        )

    s3_key = f"uploads/{current_user.id}/{uuid.uuid4().hex}/{filename}"

    try:
        s3 = _s3_client()
        upload_url: str = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
            ExpiresIn=PRESIGN_EXPIRES,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 presign hatası: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload URL oluşturulamadı. Lütfen tekrar deneyin.",
        ) from exc

    log_file = LogFile(
        user_id=current_user.id,
        filename=filename,
        s3_key=s3_key,
        size_bytes=size_bytes,
        source_type="unknown",
    )
    db.add(log_file)
    await db.commit()
    await db.refresh(log_file)

    return PresignedUploadResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        log_file_id=log_file.id,
        expires_in_seconds=PRESIGN_EXPIRES,
    )


# ── Direct multipart upload (geliştirme / S3 olmadan) ────────────────────────

@router.post(
    "/direct",
    response_model=DirectUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def direct_upload(
    file: UploadFile = File(...),
    db: DBDep = ...,
    current_user: CurrentUser = ...,
) -> DirectUploadResponse:
    """Dosyayı doğrudan backend'e yükle.

    S3 yapılandırıldıysa S3'e kaydeder, aksi hâlde lokal /tmp'ye kaydeder.
    Geliştirme ortamında CORS ve AWS credentials gerektirmez.
    """
    if file.size and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Dosya çok büyük. Maksimum {settings.max_upload_size_bytes // (1024**2)} MB.",
        )

    filename = file.filename or f"upload_{uuid.uuid4().hex}.log"
    file_id = uuid.uuid4().hex
    s3_key = f"uploads/{current_user.id}/{file_id}/{filename}"

    content = await file.read()
    size_bytes = len(content)

    if _s3_configured():
        # S3'e yükle
        try:
            s3 = _s3_client()
            s3.put_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )
            local_path = None
            logger.info("Dosya S3'e yüklendi: %s", s3_key)
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 yükleme hatası: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 yükleme başarısız. Lütfen tekrar deneyin.",
            ) from exc
    else:
        # Lokal geçici depolama
        LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        user_dir = LOCAL_UPLOAD_DIR / str(current_user.id) / file_id
        user_dir.mkdir(parents=True, exist_ok=True)
        local_path = str(user_dir / filename)
        with open(local_path, "wb") as f:
            f.write(content)
        logger.info("Dosya lokale kaydedildi: %s", local_path)

    log_file = LogFile(
        user_id=current_user.id,
        filename=filename,
        s3_key=s3_key,
        size_bytes=size_bytes,
        source_type="unknown",
        local_path=local_path,
    )
    db.add(log_file)
    await db.commit()
    await db.refresh(log_file)

    return DirectUploadResponse(
        log_file_id=log_file.id,
        filename=filename,
        size_bytes=size_bytes,
        s3_key=s3_key,
        storage="s3" if _s3_configured() else "local",
    )


# ── Liste ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[LogFileRead])
async def list_uploads(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[LogFileRead]:
    """Kullanıcının yüklediği log dosyalarını listele."""
    from sqlalchemy import select

    offset = (page - 1) * page_size
    result = await db.execute(
        select(LogFile)
        .where(LogFile.user_id == current_user.id)
        .order_by(LogFile.uploaded_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return [LogFileRead.model_validate(row) for row in result.scalars().all()]