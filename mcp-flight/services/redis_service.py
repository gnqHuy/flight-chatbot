"""
services/redis_service.py
Redis operations cho flight data.
"""
import os
import json
import uuid
import logging
import redis

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )
    return _client


TTL = int(os.getenv("REDIS_TTL", 3600))


def save_flights(flights: list[dict], prefix: str = "search") -> str:
    search_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
    get_client().setex(search_id, TTL, json.dumps(flights, ensure_ascii=False))
    logger.info(f"[Redis] Saved {len(flights)} flights → {search_id}")
    return search_id


def load_flights(search_id: str) -> list[dict] | None:
    raw = get_client().get(search_id)
    if not raw:
        return None
    return json.loads(raw)


def exists(search_id: str) -> bool:
    return bool(get_client().exists(search_id))