import os
import json
import uuid
from typing import List, Dict, Any, Optional
import redis

class RedisService:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        self.ttl_seconds = 3600 

    def save_flight_offers(self, flight_data: list | dict, parent_id: str = None) -> str:
        if parent_id:
            search_id = f"filter_{parent_id}_{uuid.uuid4().hex[:6]}"
        else:
            search_id = f"search_{uuid.uuid4().hex[:8]}"

        self.client.setex(
            name=search_id,
            time=self.ttl_seconds,
            value=json.dumps(flight_data)
        )
        return search_id

    def get_flight_offers(self, search_id: str) -> Optional[List[Dict[str, Any]]]:
        data = self.client.get(search_id)
        if data:
            return json.loads(data)
        return None

redis_service = RedisService()