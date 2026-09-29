"""
Insurance Policy Intelligence Assistant — in-memory data store.

Stores:
  policies   – dict[policy_id, PolicyRecord]
  uploads    – saves PDF bytes to ./uploads/ directory
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from app.models import PolicyRecord

# ── in-memory "database" ──────────────────────────────────────────────────────
policies: Dict[str, PolicyRecord] = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def new_id() -> str:
    return str(uuid.uuid4())


def save_policy(record: PolicyRecord) -> PolicyRecord:
    policies[record.policy_id] = record
    return record


def get_policy(policy_id: str) -> Optional[PolicyRecord]:
    return policies.get(policy_id)


def all_policies() -> list[PolicyRecord]:
    return list(policies.values())


def save_upload(policy_id: str, filename: str, data: bytes) -> str:
    """Persist uploaded PDF to disk; return the saved file path."""
    dest = os.path.join(UPLOAD_DIR, f"{policy_id}_{filename}")
    with open(dest, "wb") as f:
        f.write(data)
    return dest
