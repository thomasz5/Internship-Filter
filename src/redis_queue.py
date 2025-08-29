#!/usr/bin/env python3
"""
Redis-backed simple FIFO queue for company names and deduplication set.
"""

import json
from typing import Optional

import redis

from config import Config


class CompanyQueue:
    def __init__(self, redis_url: Optional[str] = None):
        self.config = Config()
        self.redis = redis.from_url(redis_url or self.config.REDIS_URL, decode_responses=True)
        self.queue_key = self.config.REDIS_QUEUE_KEY
        self.seen_key = self.config.REDIS_SEEN_SET_KEY

    def enqueue_company(self, company_name: str) -> bool:
        """Enqueue a company if not already seen. Returns True if enqueued."""
        company = (company_name or '').strip()
        if not company:
            return False
        # Use a lowercased normalized company for dedup
        normalized = company.lower()
        # sadd returns 1 if added, 0 if already present
        added = self.redis.sadd(self.seen_key, normalized)
        if added:
            payload = json.dumps({"company": company})
            # RPUSH for FIFO, consumer will BLPOP
            self.redis.rpush(self.queue_key, payload)
            return True
        return False

    def dequeue_company(self, block: bool = True, timeout_seconds: int = 5) -> Optional[str]:
        """Dequeue next company; blocks by default with timeout. Returns company name or None."""
        if block:
            result = self.redis.blpop(self.queue_key, timeout=timeout_seconds)
            if not result:
                return None
            _, payload = result
        else:
            payload = self.redis.lpop(self.queue_key)
            if not payload:
                return None
        try:
            data = json.loads(payload)
            return (data.get("company") or '').strip() or None
        except Exception:
            return None

    def size(self) -> int:
        return int(self.redis.llen(self.queue_key))

    def clear(self):
        self.redis.delete(self.queue_key)
        self.redis.delete(self.seen_key)


if __name__ == "__main__":
    q = CompanyQueue()
    print("Queue size:", q.size())

