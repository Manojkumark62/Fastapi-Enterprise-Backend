import httpx
from pydantic import BaseModel


class ExternalAPIError(Exception):
    pass


async def fetch_json(url: str, *, params: dict | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ExternalAPIError("External response must be a JSON object")
            return data
    except (httpx.HTTPError, ValueError) as exc:
        raise ExternalAPIError("External service request failed") from exc


async def fetch_and_transform(
    url: str, response_model: type[BaseModel], *, params: dict | None = None
) -> BaseModel:
    """Fetch a third-party object and validate it into an internal schema."""
    data = await fetch_json(url, params=params)
    try:
        return response_model.model_validate(data)
    except ValueError as exc:
        raise ExternalAPIError("External response did not match the expected schema") from exc