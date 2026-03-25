from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini_analyzer import analyze_image_with_gemini
from app.core.hive_moderation import analyze_media_hive
from app.core.fact_checker import query_fact_check_api
from app.core.auth import check_daily_limit
from app.core.database import get_db
from app.models.schemas import AnalysisResponse
from app.models.user import User
from app.models.history import VerificationLog, QueryType

router = APIRouter()

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "video/mp4", "video/webm",
    "audio/mpeg", "audio/wav", "audio/ogg",
}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=AnalysisResponse)
async def analyze_upload(
    file: UploadFile      = File(...),
    user: User            = Depends(check_daily_limit),
    db:   AsyncSession    = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Formato não suportado.")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande (máx 10 MB).")

    is_image = file.content_type.startswith("image/")

    # Run Hive + Gemini in parallel
    import asyncio
    hive_task   = asyncio.create_task(analyze_media_hive(data, file.content_type))
    gemini_task = asyncio.create_task(
        analyze_image_with_gemini(data, file.content_type) if is_image
        else _audio_video_gemini_fallback(file.content_type)
    )
    hive_result, ai = await asyncio.gather(hive_task, gemini_task)

    # Merge scores
    base_score = int(ai.get("score", 50))

    # Hive AI-probability lowers credibility score
    if hive_result.get("available") and hive_result.get("ai_probability") is not None:
        hive_ai_prob = hive_result["ai_probability"]
        if hive_ai_prob > 0.85:
            base_score = min(base_score, 20)
        elif hive_ai_prob > 0.65:
            base_score = min(base_score, 42)
        elif hive_ai_prob < 0.15:
            base_score = max(base_score, 65)

    final_score = max(0, min(100, base_score))
    verdict = "CONFIÁVEL" if final_score >= 68 else "SUSPEITO" if final_score >= 38 else "FALSO"

    result = AnalysisResponse(
        score              =final_score,
        semantic_score     =int(ai.get("semantic_score", 50)),
        domain_score       =72,
        sensationalism     =int(ai.get("sensationalism", 50)),
        verdict            =verdict,
        summary            =ai.get("summary", ""),
        red_flags          =ai.get("red_flags", []),
        positive_signals   =ai.get("positive_signals", []),
        logical_fallacies  =ai.get("logical_fallacies", []),
        emotional_triggers =bool(ai.get("emotional_triggers", False)),
        fact_checks        =[],
        domain_note        ="Arquivo enviado diretamente.",
        recommended_sources=ai.get("recommended_sources", []),
        hive_result        =hive_result,
    )

    log = VerificationLog(
        user_id    =user.id,
        query_type =QueryType.IMAGE,
        query_input=file.filename or "upload"[:500],
        result     =result.model_dump(),
        score      =result.score,
        verdict    =result.verdict,
        summary    =result.summary,
    )
    db.add(log)
    await db.commit()
    return result


async def _audio_video_gemini_fallback(content_type: str) -> dict:
    """Gemini 2.5 Flash doesn't support raw audio/video bytes — return neutral."""
    return {
        "score": 50, "semantic_score": 50, "sensationalism": 50,
        "verdict": "SUSPEITO",
        "summary": "Análise de áudio/vídeo via Hive concluída. Análise semântica por texto não aplicável.",
        "red_flags": [], "positive_signals": [], "logical_fallacies": [],
        "emotional_triggers": False, "temporal_issues": False, "recommended_sources": [],
    }
