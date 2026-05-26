"""Fuente: OpenRouter API — modelos nuevos en los últimos N días."""

import logging
import os
from datetime import datetime, timezone, timedelta

import httpx

from models.schemas import ModelEntry

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


async def fetch_new_models(days: int = 7) -> tuple[list[ModelEntry], str | None]:
    """Devuelve modelos agregados a OpenRouter en los últimos `days` días.

    Returns:
        (lista de modelos, error message o None si OK)
    """
    if not OPENROUTER_API_KEY:
        return [], "OPENROUTER_API_KEY no configurada"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                OPENROUTER_MODELS_URL,
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            )
        response.raise_for_status()
    except Exception as e:
        logger.error("OpenRouter API error: %s", e)
        return [], f"OpenRouter: {e}"

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    models: list[ModelEntry] = []

    for m in response.json().get("data", []):
        # created es unix timestamp
        created_ts = m.get("created", 0)
        if not created_ts:
            continue
        created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
        if created_dt < cutoff:
            continue

        pricing = m.get("pricing", {})
        try:
            price_in = float(pricing.get("prompt", 0)) * 1_000_000
            price_out = float(pricing.get("completion", 0)) * 1_000_000
        except (TypeError, ValueError):
            price_in = price_out = 0.0

        context_length = m.get("context_length", 0)

        # Extraer nombre del provider del model id (ej: "openai/gpt-4o" → "openai")
        model_id = m.get("id", "")
        provider = model_id.split("/")[0] if "/" in model_id else "unknown"
        model_name = m.get("name", model_id)

        models.append(ModelEntry(
            name=model_name,
            provider=provider,
            context_k=round(context_length / 1000),
            price_input=round(price_in, 4),
            price_output=round(price_out, 4),
            created_date=created_dt.strftime("%Y-%m-%d"),
        ))

    # Ordenar del más reciente al más viejo
    models.sort(key=lambda x: x.created_date, reverse=True)
    logger.info("OpenRouter: %d modelos nuevos en los últimos %d días", len(models), days)
    return models, None
