from __future__ import annotations

from services.subscriptions import TIERS


def format_balance(user: object) -> str:
    tier = user["tier"]  # type: ignore[index]
    tier_info = TIERS.get(tier, TIERS["free"])
    return (
        f"💳 <b>Баланс:</b> {user['credits']} кредитов\n"  # type: ignore[index]
        f"{tier_info['emoji']} <b>Тариф:</b> {tier_info['label']}"
    )


def format_generation_result(credits_remaining: int) -> str:
    return f"✅ Готово! Осталось кредитов: <b>{credits_remaining}</b>"


def format_stats(
    users_count: int,
    gens_24h: int,
    gens_7d: int,
) -> str:
    return (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🎨 Генераций за 24ч: <b>{gens_24h}</b>\n"
        f"🎨 Генераций за 7 дней: <b>{gens_7d}</b>"
    )
