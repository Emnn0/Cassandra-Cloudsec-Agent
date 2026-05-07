"""Celery task: full log analysis pipeline.

Steps:
  1. Download log file from S3 (or read local path)
  2. Detect parser type (Cloudflare Firewall / HTTP)
  3. Parse events -> List[NormalizedEvent]
  4. Heuristic analysis -> HeuristicReport
  5. LLM reasoning -> ThreatReport
  6. Persist both reports to DB; update Analysis status
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from celery_app import celery_app

logger = logging.getLogger(__name__)


def _make_session() -> async_sessionmaker[AsyncSession]:
    """Her Celery task çağrısında yeni event loop'a bağlı taze engine oluştur.

    Celery fork'larken asyncio.run() yeni bir loop açar; modül seviyesinde
    oluşturulan global engine eski loop'a bağlı kalır ve 'Future attached to
    a different loop' hatasına yol açar. Bu fonksiyon her seferinde taze
    bağlantı havuzu yaratır.
    """
    from app.config import get_settings
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=2,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, name="analyze_log_file_task", max_retries=2, default_retry_delay=30)
def analyze_log_file_task(self, analysis_id: int) -> dict:
    """Entry point — runs the async pipeline in a dedicated event loop."""
    return asyncio.run(_run(analysis_id))


async def _run(analysis_id: int) -> dict:
    from app.config import get_settings
    from app.db.models import Analysis, AnalysisStatus, LogFile
    from app.schemas.report import HeuristicReport
    from app.services.analyzer.heuristics import analyze as run_heuristics
    from app.services.analyzer.reasoning import generate_threat_report
    from app.services.llm.anthropic_provider import AnthropicProvider
    from app.services.parsers.registry import detect_parser

    settings = get_settings()
    AsyncSessionLocal = _make_session()

    async with AsyncSessionLocal() as db:
        # ── Analysis + LogFile yükle ──────────────────────────────────────────
        result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if analysis is None:
            logger.error("Analysis %d not found", analysis_id)
            return {"error": "analysis_not_found"}

        log_file_result = await db.execute(
            select(LogFile).where(LogFile.id == analysis.log_file_id)
        )
        log_file = log_file_result.scalar_one()

        analysis.status = AnalysisStatus.processing
        analysis.started_at = datetime.now(timezone.utc)
        analysis.progress_step = 1  # Dosya hazırlanıyor
        await db.commit()

        async def _fail(msg: str) -> dict:
            analysis.status = AnalysisStatus.failed
            analysis.error_message = msg
            analysis.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.error("Analysis %d failed: %s", analysis_id, msg)
            return {"error": msg}

        # ── Step 1: Dosyayı hazırla ───────────────────────────────────────────
        s3_configured = bool(settings.aws_access_key_id and settings.aws_secret_access_key)
        _local_tmp = False

        if log_file.local_path and os.path.exists(log_file.local_path):
            tmp_path = log_file.local_path
            logger.info("Analysis %d: lokal dosya: %s", analysis_id, tmp_path)
        elif s3_configured:
            try:
                s3 = boto3.client(
                    "s3",
                    region_name=settings.aws_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
                    tmp_path = tmp.name
                s3.download_file(settings.s3_bucket_name, log_file.s3_key, tmp_path)
                _local_tmp = True
                logger.info("Analysis %d: S3'ten indirildi", analysis_id)
            except (BotoCoreError, ClientError) as exc:
                return await _fail(f"S3 indirme hatası: {exc}")
        else:
            return await _fail("Dosya bulunamadı: lokal yol yok ve S3 yapılandırılmamış.")

        try:
            # ── Step 2: Parser tespiti ────────────────────────────────────────
            try:
                parser = detect_parser(tmp_path)
            except ValueError as exc:
                return await _fail(f"Bilinmeyen log formatı: {exc}")

            log_file.source_type = type(parser).__name__.replace("Parser", "").lower()
            analysis.progress_step = 2  # Log olayları ayrıştırılıyor
            await db.commit()

            # ── Step 3: Event ayrıştırma ──────────────────────────────────────
            try:
                events = list(parser.parse(tmp_path))
            except Exception as exc:
                return await _fail(f"Parse hatası: {exc}")

            if not events:
                return await _fail("Log dosyasında ayrıştırılabilir olay bulunamadı.")

            logger.info("Analysis %d: %d olay ayrıştırıldı", analysis_id, len(events))

            # ── Step 4: Buluşsal analiz ───────────────────────────────────────
            analysis.progress_step = 3  # Buluşsal analiz çalıştırılıyor
            await db.commit()
            try:
                heuristic_report = run_heuristics(events)
            except Exception as exc:
                return await _fail(f"Buluşsal analiz hatası: {exc}")

            # ── Step 5: Buluşsal raporu hemen kaydet ─────────────────────────
            analysis.heuristic_report = heuristic_report.model_dump(mode="json")
            analysis.progress_step = 4  # Yapay zeka analisti devreye giriyor
            await db.commit()
            logger.info("Analysis %d: buluşsal rapor kaydedildi.", analysis_id)

            # ── Step 6: LLM tehdit analizi ────────────────────────────────────
            try:
                provider = AnthropicProvider(
                    api_key=settings.anthropic_api_key or None,
                    base_url=settings.anthropic_base_url or None,
                    model=settings.llm_model or None,
                )
                threat_report = await generate_threat_report(heuristic_report, provider)
            except Exception as exc:
                err_msg = str(exc)
                # Geçici servis hatası → kısmi başarı olarak kaydet
                if any(k in err_msg for k in ("temporarily unavailable", "Connection error", "service_error", "overloaded")):
                    logger.warning("Analysis %d: LLM geçici hata, kısmi sonuç kaydediliyor: %s", analysis_id, err_msg)
                    analysis.status = AnalysisStatus.completed
                    analysis.error_message = f"LLM geçici olarak kullanılamadı: {err_msg[:200]}"
                    analysis.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    return {"status": "partial", "analysis_id": analysis_id}
                return await _fail(f"LLM analiz hatası: {exc}")

            # ── Step 7: Tehdit raporunu kaydet ───────────────────────────────
            analysis.threat_report = threat_report.model_dump(mode="json")
            analysis.status = AnalysisStatus.completed
            analysis.progress_step = 5  # Tamamlandı
            analysis.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info("Analysis %d tamamlandı.", analysis_id)
            return {"status": "completed", "analysis_id": analysis_id}

        finally:
            if _local_tmp and os.path.exists(tmp_path):
                os.unlink(tmp_path)