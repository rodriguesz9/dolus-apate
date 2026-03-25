from fastapi import APIRouter, Depends, HTTPException
import httpx
from bs4 import BeautifulSoup
import re

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import UrlRequest, AnalysisResponse
from app.core.pipeline import run_pipeline
from app.core.security import sanitize
from app.core.auth import check_daily_limit
from app.core.database import get_db
from app.models.user import User
from app.models.history import VerificationLog, QueryType

router = APIRouter()
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VerifAIBot/1.0)"}


async def fetch_page_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
    return text[:4000]


@router.post("/check-url", response_model=AnalysisResponse)
async def check_url(
    body: UrlRequest,
    user: User         = Depends(check_daily_limit),
    db:   AsyncSession = Depends(get_db),
):
    url = sanitize(body.url.strip())
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        page_text = await fetch_page_text(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Não foi possível acessar a URL: {str(exc)[:100]}")

    if len(page_text) < 50:
        raise HTTPException(status_code=422, detail="Conteúdo insuficiente para análise.")

    result = await run_pipeline(text=page_text, url=url)

    log = VerificationLog(
        user_id    =user.id,
        query_type =QueryType.URL,
        query_input=url[:500],
        result     =result.model_dump(),
        score      =result.score,
        verdict    =result.verdict,
        summary    =result.summary,
    )
    db.add(log)
    await db.commit()
    return result
