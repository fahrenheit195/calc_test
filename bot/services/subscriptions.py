from __future__ import annotations

TIERS: dict[str, dict] = {
    "free": {
        "generation_cost": 3,
        "daily_credits": 3,
        "rate_multiplier": 1,
        "label": "Free",
        "emoji": "🆓",
    },
    "basic": {
        "generation_cost": 2,
        "daily_credits": 10,
        "rate_multiplier": 2,
        "label": "Basic",
        "emoji": "⭐",
    },
    "premium": {
        "generation_cost": 1,
        "daily_credits": 30,
        "rate_multiplier": 5,
        "label": "Premium",
        "emoji": "💎",
    },
}

CREDIT_PACKS = [
    {"id": "pack_50", "credits": 50, "stars": 50, "label": "50 кредитов — 50 ⭐"},
    {"id": "pack_150", "credits": 150, "stars": 100, "label": "150 кредитов — 100 ⭐"},
    {"id": "pack_500", "credits": 500, "stars": 250, "label": "500 кредитов — 250 ⭐"},
]

SUBSCRIPTION_PACKS = [
    {"id": "sub_basic", "tier": "basic", "stars": 150, "label": "Basic на 30 дней — 150 ⭐"},
    {"id": "sub_premium", "tier": "premium", "stars": 400, "label": "Premium на 30 дней — 400 ⭐"},
]


def get_generation_cost(tier: str) -> int:
    return TIERS.get(tier, TIERS["free"])["generation_cost"]


def get_daily_credits(tier: str) -> int:
    return TIERS.get(tier, TIERS["free"])["daily_credits"]


def get_rate_multiplier(tier: str) -> int:
    return TIERS.get(tier, TIERS["free"])["rate_multiplier"]


def get_pack_by_id(pack_id: str) -> dict | None:
    for p in CREDIT_PACKS:
        if p["id"] == pack_id:
            return p
    return None


def get_sub_by_id(sub_id: str) -> dict | None:
    for s in SUBSCRIPTION_PACKS:
        if s["id"] == sub_id:
            return s
    return None
