"""Read quotes from the selected provider endpoints."""

import requests

from llm_transitivity.domain.config import ModelSpec


def provider_quote(model: ModelSpec) -> tuple[str, dict]:
    url = f"https://openrouter.ai/api/v1/models/{model.identifier}/endpoints"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    endpoints = [
        e
        for e in response.json()["data"]["endpoints"]
        if e.get("tag") == model.provider
    ]
    if len(endpoints) != 1:
        raise ValueError(
            f"{model.identifier}: expected exactly one published endpoint for {model.provider}"
        )
    pricing = endpoints[0]["pricing"]
    return url, pricing
