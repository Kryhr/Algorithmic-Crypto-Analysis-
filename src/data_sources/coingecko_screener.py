"""
Universe screener: uses CoinGecko market data (NOT orderflow) to find coins
that are real price-discovery assets, listed on major exchanges, with
market-cap ranks and volume/mcap ratios in the "semi-main but illiquid" zone.

Orderflow itself (order book depth, trade tape) has to come from an exchange
directly - see binance_orderflow.py.
"""
import sys

import requests

from src.config import COINGECKO_API_KEY, COINGECKO_BASE_URL

HEADERS = {"x-cg-demo-api-key": COINGECKO_API_KEY}

# categories that aren't genuine price-discovery assets for this kind of study
EXCLUDED_CATEGORIES = {
    "stablecoins",
    "exchange-based-tokens",
    "real-world-assets-rwa",
    "rwa-protocol",
    "tokenized-products",
    "tokenized-treasuries",
    "tokenized-t-bills",
    "tokenized-treasury-bonds-t-bonds",
    "tokenized-money-market-fund-mmfs",
    "tokenized-gold",
    "tokenized-silver",
    "tokenized-commodities",
    "tokenized-bank-deposit",
    "wrapped-tokens",
}

# volume floor: filters out instruments with no real organic trading (RWA
# funds, near-dormant tokens) that would otherwise falsely look "illiquid"
MIN_VOLUME_USD = 5_000_000


def _excluded_ids() -> set[str]:
    excluded = set()
    for category_id in EXCLUDED_CATEGORIES:
        resp = requests.get(
            f"{COINGECKO_BASE_URL}/coins/markets",
            headers=HEADERS,
            params={"vs_currency": "usd", "category": category_id, "per_page": 250},
            timeout=15,
        )
        resp.raise_for_status()
        excluded.update(c["id"] for c in resp.json())
    return excluded


def screen(rank_min: int = 30, rank_max: int = 150, top_n: int = 25) -> list[dict]:
    """Return candidate coins sorted by ascending volume/market_cap ratio
    (i.e. thinnest relative liquidity first) within the given rank window."""
    resp = requests.get(
        f"{COINGECKO_BASE_URL}/coins/markets",
        headers=HEADERS,
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false",
        },
        timeout=15,
    )
    resp.raise_for_status()
    coins = resp.json()

    excluded = _excluded_ids()

    candidates = []
    for c in coins:
        rank = c.get("market_cap_rank")
        mcap = c.get("market_cap")
        vol = c.get("total_volume")
        if rank is None or mcap is None or vol is None or mcap == 0:
            continue
        if not (rank_min <= rank <= rank_max):
            continue
        if c["id"] in excluded:
            continue
        if vol < MIN_VOLUME_USD:
            continue
        candidates.append(
            {
                "id": c["id"],
                "symbol": c["symbol"].upper(),
                "rank": rank,
                "market_cap": mcap,
                "volume_24h": vol,
                "vol_mcap_ratio": vol / mcap,
            }
        )

    candidates.sort(key=lambda x: x["vol_mcap_ratio"])
    return candidates[:top_n]


if __name__ == "__main__":
    for row in screen():
        print(
            f"{row['rank']:>4} {row['symbol']:<8} "
            f"mcap=${row['market_cap']/1e6:,.0f}M "
            f"vol=${row['volume_24h']/1e6:,.0f}M "
            f"vol/mcap={row['vol_mcap_ratio']:.3f}"
        )
    sys.exit(0)
