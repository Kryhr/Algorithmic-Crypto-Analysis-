import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Binance.com's public WS/REST is geo-blocked for US IPs (HTTP 451).
# Coinbase Exchange's public market-data feed is free, keyless, and not
# geo-restricted in the US - use that for orderflow capture instead.
COINBASE_WS_URL = "wss://ws-feed.exchange.coinbase.com"

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
