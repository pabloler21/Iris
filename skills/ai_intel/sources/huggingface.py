"""Fuente: HuggingFace API — modelos nuevos de organizaciones conocidas (sin API key).

Filtra por organizaciones/autores con trayectoria en modelos de lenguaje para
evitar noise de modelos privados o de baja calidad de la comunidad general.
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import ModelEntry

logger = logging.getLogger(__name__)

HF_MODELS_URL = "https://huggingface.co/api/models"

# Organizaciones de referencia en AI — sus modelos siempre son relevantes
KNOWN_ORGS = {
    "google", "meta-llama", "mistralai", "Qwen", "deepseek-ai",
    "microsoft", "cohere", "ai21-labs", "allenai", "EleutherAI",
    "tiiuae", "bigscience", "stabilityai", "openai", "anthropic",
    "01-ai", "internlm", "baichuan-inc", "THUDM", "NousResearch",
}


async def fetch_new_models(days: int = 7, limit: int = 8) -> tuple[list[ModelEntry], str | None]:
    """Devuelve modelos nuevos en HuggingFace de organizaciones conocidas.

    Solo incluye modelos de texto generativo (text-generation) de orgs reconocidas,
    para evitar el ruido de miles de fine-tunes anónimos que se publican diariamente.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                HF_MODELS_URL,
                params={
                    "filter": "text-generation",
                    "sort": "createdAt",
                    "direction": -1,
                    "limit": 100,  # traemos más para poder filtrar por org
                },
            )
        response.raise_for_status()
    except Exception as e:
        logger.error("HuggingFace API error: %s", e)
        return [], f"HuggingFace: {e}"

    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days)
    models: list[ModelEntry] = []

    for m in response.json():
        created_str = m.get("createdAt", "")
        if not created_str:
            continue
        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_dt < cutoff_dt:
            break  # lista ordenada por fecha → podemos parar

        model_id = m.get("modelId") or m.get("id", "")
        # Extraer organización del model_id (ej: "google/gemma-3" → "google")
        org = model_id.split("/")[0] if "/" in model_id else ""

        # Solo incluir orgs conocidas
        if org not in KNOWN_ORGS:
            continue

        models.append(ModelEntry(
            name=model_id,
            provider="huggingface",
            context_k=0,
            price_input=0.0,
            price_output=0.0,
            created_date=created_dt.strftime("%Y-%m-%d"),
        ))

        if len(models) >= limit:
            break

    logger.info("HuggingFace: %d modelos nuevos de orgs conocidas en %d días", len(models), days)
    return models, None
