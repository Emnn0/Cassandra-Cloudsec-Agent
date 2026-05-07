"""Analysis endpoints.

POST /api/v1/analyses        — kick off analysis Celery task
GET  /api/v1/analyses        — list user's analyses (paginated)
GET  /api/v1/analyses/{id}   — get status + reports
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DBDep
from app.db.models import Analysis, AnalysisStatus, LogFile
from app.schemas.analysis import AnalysisCreate, AnalysisListResponse, AnalysisRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=AnalysisRead, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    body: AnalysisCreate,
    db: DBDep,
    current_user: CurrentUser,
) -> AnalysisRead:
    """Create an Analysis record and enqueue the Celery processing task."""
    # Verify the log file belongs to this user
    result = await db.execute(
        select(LogFile).where(
            LogFile.id == body.log_file_id,
            LogFile.user_id == current_user.id,
        )
    )
    log_file = result.scalar_one_or_none()
    if log_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LogFile {body.log_file_id} not found.",
        )

    analysis = Analysis(
        log_file_id=log_file.id,
        status=AnalysisStatus.pending,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Enqueue — import here to avoid circular import at module load
    from app.tasks.analyze import analyze_log_file_task

    analyze_log_file_task.delay(analysis.id)
    logger.info("Analysis %d enqueued for log_file %d", analysis.id, log_file.id)

    return AnalysisRead.model_validate(analysis)


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AnalysisListResponse:
    """Return paginated list of analyses for the current user."""
    offset = (page - 1) * page_size

    # Join to LogFile to filter by user
    base_query = (
        select(Analysis)
        .join(LogFile, Analysis.log_file_id == LogFile.id)
        .where(LogFile.user_id == current_user.id)
    )

    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = total_result.scalar_one()

    items_result = await db.execute(
        base_query.order_by(Analysis.id.desc()).offset(offset).limit(page_size)
    )
    items = [AnalysisRead.model_validate(row) for row in items_result.scalars().all()]

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: int,
    db: DBDep,
    current_user: CurrentUser,
) -> AnalysisRead:
    """Return analysis status and, when complete, the full reports."""
    result = await db.execute(
        select(Analysis)
        .join(LogFile, Analysis.log_file_id == LogFile.id)
        .where(
            Analysis.id == analysis_id,
            LogFile.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found.",
        )
    return AnalysisRead.model_validate(analysis)


@router.get("/{analysis_id}/report.pdf", response_class=Response)
async def download_pdf_report(
    analysis_id: int,
    db: DBDep,
    current_user: CurrentUser,
) -> Response:
    """Generate and stream a PDF threat report for a completed analysis."""
    result = await db.execute(
        select(Analysis)
        .join(LogFile, Analysis.log_file_id == LogFile.id)
        .where(
            Analysis.id == analysis_id,
            LogFile.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    if analysis.status != AnalysisStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Analysis is not completed yet (status: {analysis.status}).",
        )
    if not analysis.threat_report or not analysis.heuristic_report:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Analysis completed but report data is missing.",
        )

    from app.schemas.report import HeuristicReport
    from app.schemas.threat_report import ThreatReport
    from app.services.report.generator import generate_pdf

    threat = ThreatReport.model_validate(analysis.threat_report)
    heuristic = HeuristicReport.model_validate(analysis.heuristic_report)

    pdf_bytes = generate_pdf(threat, heuristic)

    filename = f"loglens-threat-report-{analysis_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
