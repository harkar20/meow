import httpx

from ..config import settings


async def call_ml_service(endpoint: str, payload: dict, timeout: float = 10.0) -> dict:
    # Why: keep ML proxy logic in one place so routes stay thin and easier to maintain.
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{settings.ML_SERVICE_URL}/ml/{endpoint}", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        print(f"[ML call failed] {endpoint}: {exc}")
        return {}
