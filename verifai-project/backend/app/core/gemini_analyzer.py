import os
import json
import re
from datetime import datetime

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# ── Always inject current date so the model doesn't think it's 2024 ───────────
_TODAY = datetime.now().strftime("%d de %B de %Y")   # e.g. "25 de março de 2026"

SYSTEM_INSTRUCTION = f"""Você é um sistema especializado em detecção de desinformação e análise forense de conteúdo digital.

CONTEXTO TEMPORAL OBRIGATÓRIO:
- DATA DE HOJE: {_TODAY}
- YEAR ATUAL: {datetime.now().year}
- Eventos, eleições, descobertas e acontecimentos ocorridos até esta data já são PASSADO.
- Trate qualquer evento de 2025 ou 2026 como JÁ OCORRIDO, não como futuro.

Seu papel: analisar conteúdos e retornar APENAS JSON válido (sem markdown, sem texto extra).
"""

_ANALYSIS_SCHEMA = """
{
  "score": <inteiro 0-100, credibilidade geral>,
  "semantic_score": <inteiro 0-100, coerência e rigor semântico>,
  "sensationalism": <inteiro 0-100, grau de sensacionalismo>,
  "verdict": "<CONFIÁVEL | SUSPEITO | FALSO>",
  "summary": "<análise objetiva em 2 frases>",
  "red_flags": ["<item>"],
  "positive_signals": ["<item>"],
  "logical_fallacies": ["<item>"],
  "emotional_triggers": <true | false>,
  "temporal_issues": <true | false>,
  "recommended_sources": ["<fonte confiável para verificar>"]
}

Critérios de pontuação:
- score >= 68 → CONFIÁVEL
- score 38-67 → SUSPEITO
- score < 38  → FALSO

Avalie rigorosamente: precisão factual, coerência interna, tom, fontes citadas, falácias, gatilhos emocionais, linguagem alarmista, inconsistências temporais.
"""


def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )


def _safe_parse(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    # Sometimes model wraps in outer object
    try:
        return json.loads(raw)
    except Exception:
        # Try to extract JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


async def analyze_with_gemini(text: str) -> dict:
    """Semantic analysis of text using Gemini 2.5 Flash."""
    try:
        model = _get_model()
        prompt = f"Analise o conteúdo abaixo e retorne APENAS o JSON com a estrutura:\n{_ANALYSIS_SCHEMA}\n\nConteúdo:\n\"\"\"\n{text[:3000]}\n\"\"\""
        response = model.generate_content(prompt)
        return _safe_parse(response.text)
    except Exception as e:
        return {
            "score": 50,
            "semantic_score": 50,
            "sensationalism": 50,
            "verdict": "SUSPEITO",
            "summary": f"Análise de IA parcialmente indisponível. {str(e)[:60]}",
            "red_flags": ["Análise de IA não concluída"],
            "positive_signals": [],
            "logical_fallacies": [],
            "emotional_triggers": False,
            "temporal_issues": False,
            "recommended_sources": [],
        }


async def analyze_image_with_gemini(image_bytes: bytes, mime_type: str) -> dict:
    """Vision analysis of an image using Gemini 2.5 Flash."""
    import base64
    b64 = base64.b64encode(image_bytes).decode()

    prompt = f"""Você é um perito forense digital. DATA ATUAL: {_TODAY}.
Analise esta imagem para detectar deepfakes, manipulações e geração por IA.
Retorne APENAS o JSON:
{_ANALYSIS_SCHEMA}
Verifique: artefatos de IA/GAN, inconsistências de iluminação/sombra, geração sintética, metadados visuais, imagem fora de contexto."""

    try:
        model = _get_model()
        response = model.generate_content([
            {"mime_type": mime_type, "data": b64},
            prompt,
        ])
        return _safe_parse(response.text)
    except Exception as e:
        return {
            "score": 50, "semantic_score": 50, "sensationalism": 50,
            "verdict": "SUSPEITO",
            "summary": f"Análise de imagem não concluída: {str(e)[:60]}",
            "red_flags": ["Gemini Vision indisponível"],
            "positive_signals": [], "logical_fallacies": [],
            "emotional_triggers": False, "temporal_issues": False,
            "recommended_sources": [],
        }
