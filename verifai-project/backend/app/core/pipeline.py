from app.core.gemini_analyzer import analyze_with_gemini
from app.core.fact_checker import query_fact_check_api
from app.core.domain_checker import check_domain_reputation
from app.models.schemas import AnalysisResponse


async def run_pipeline(text: str, url: str | None = None) -> AnalysisResponse:
    """
    Progressive Verification Pipeline:
      Layer 1 – Fact Check agencies (Google Fact Check API)
      Layer 2 – Domain reputation heuristic
      Layer 3 – Gemini 2.5 Flash semantic analysis
    """
    # Layer 1
    fact_checks = await query_fact_check_api(text[:200])

    # Layer 2
    if url:
        domain_info = check_domain_reputation(url)
    else:
        domain_info = {"score": 72, "note": "Texto direto – análise de fonte não aplicável.", "hostname": None}

    # Layer 3
    ai = await analyze_with_gemini(text)

    # Merge
    base_score = int(ai.get("score", 50))

    for fc in fact_checks:
        rating_lower = fc.rating.lower()
        if any(k in rating_lower for k in ["falso", "false", "incorreto", "mislead", "enganoso"]):
            base_score = min(base_score, 22)
        elif any(k in rating_lower for k in ["verdadeiro", "true", "correto", "accurate", "confirmado"]):
            base_score = max(base_score, 75)

    d_score = domain_info["score"]
    if d_score < 30:
        base_score = int(base_score * 0.75)
    elif d_score >= 85:
        base_score = min(100, int(base_score * 1.1))

    final_score = max(0, min(100, base_score))
    verdict = "CONFIÁVEL" if final_score >= 68 else "SUSPEITO" if final_score >= 38 else "FALSO"

    return AnalysisResponse(
        score=final_score,
        semantic_score=int(ai.get("semantic_score", 50)),
        domain_score=d_score,
        sensationalism=int(ai.get("sensationalism", 50)),
        verdict=verdict,
        summary=ai.get("summary", ""),
        red_flags=ai.get("red_flags", []),
        positive_signals=ai.get("positive_signals", []),
        logical_fallacies=ai.get("logical_fallacies", []),
        emotional_triggers=bool(ai.get("emotional_triggers", False)),
        fact_checks=fact_checks,
        domain_note=domain_info["note"],
        source_url=url,
        recommended_sources=ai.get("recommended_sources", []),
    )
