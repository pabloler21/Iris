"""Fuente: HuggingFace API — modelos nuevos/trending (sin API key)."""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import ModelEntry

logger = logging.getLogger(__name__)

HF_MODELS_URL = "https://huggingface.co/api/models"


async def fetch_new_models(days: int = 7, limit: int = 10) -> tuple[list[ModelEntry], str | None]:
    """Devuelve modelos nuevos en HuggingFace en los últimos `days` días.

    Filtra por modelos de text-generation (LLMs) con más downloads recientes.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                HF_MODELS_URL,
                params={
                    "filter": "text-generation",
                    "sort": "createdAt",
                    "direction": -1,
                    "limit": limit * 3,  # pedimos más para poder filtrar por fecha
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
            continue

        model_id = m.get("modelId") or m.get("id", "")
        # HuggingFace no da pricing — dejamos en 0
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

    logger.info("HuggingFace: %d modelos nuevos en los últimos %d días", len(models), days)
    return models, None
