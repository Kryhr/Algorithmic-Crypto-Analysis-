"""
Free bulk historical data from Binance's public data archive
(data.binance.vision). Unlike api.binance.com/stream.binance.com, this
archive is NOT geo-blocked for US IPs - it's just static file storage.

Two datasets, both real orderflow (not aggregated OHLCV):
  - spot daily trades   : every individual trade, tick-by-tick, with side.
                           History starts at each symbol's spot listing date.
  - futures bookDepth   : periodic order-book depth snapshots at +-1%..5%
                           from mid-price, ~every 30s. History starts 2023-01-01.
                           Futures market, used here as a liquidity proxy for
                           the same underlying asset - there's no free
                           historical *spot* order-book depth anywhere.
"""
import io
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from src.config import DATA_DIR

ARCHIVE_BASE = "https://data.binance.vision/data"

TRADES_COLUMNS = [
    "trade_id", "price", "qty", "quote_qty", "timestamp", "is_buyer_maker", "is_best_match",
]
BOOK_DEPTH_COLUMNS = ["timestamp", "percentage", "depth", "notional"]


def _daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _fetch_daily_csv(url: str, columns: list[str]) -> pd.DataFrame | None:
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return None
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as f:
            first_byte = f.read(1)
            f.seek(0)
            has_header = first_byte.isalpha()
            df = pd.read_csv(f, header=0 if has_header else None, names=None if has_header else columns)
    return df


def download_trades(symbol: str, start: date, end: date, market: str = "spot") -> pd.DataFrame:
    """Tick-by-tick trade tape for `symbol` (e.g. 'ALGOUSDT') between start/end (inclusive)."""
    frames = []
    for d in _daterange(start, end):
        url = f"{ARCHIVE_BASE}/{market}/daily/trades/{symbol}/{symbol}-trades-{d.isoformat()}.zip"
        df = _fetch_daily_csv(url, TRADES_COLUMNS)
        if df is not None:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=TRADES_COLUMNS)
    out = pd.concat(frames, ignore_index=True)
    # Binance switched trade-archive timestamps from milliseconds to
    # microseconds partway through 2025; infer per-row by magnitude
    # (ms epoch ~1.7e12 today, us epoch ~1.7e15) rather than assume one unit.
    is_micros = out["timestamp"] > 1e14
    out["timestamp"] = pd.to_datetime(
        out["timestamp"].where(~is_micros) , unit="ms"
    ).fillna(pd.to_datetime(out["timestamp"].where(is_micros), unit="us"))
    return out


def download_book_depth(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Periodic +-1..5% order-book depth snapshots for `symbol` (futures only, e.g. 'ALGOUSDT')."""
    frames = []
    for d in _daterange(start, end):
        url = f"{ARCHIVE_BASE}/futures/um/daily/bookDepth/{symbol}/{symbol}-bookDepth-{d.isoformat()}.zip"
        df = _fetch_daily_csv(url, BOOK_DEPTH_COLUMNS)
        if df is not None:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=BOOK_DEPTH_COLUMNS)
    out = pd.concat(frames, ignore_index=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    return out


def backfill(symbol: str, start: date, end: date) -> None:
    """Download both datasets for `symbol` and save as parquet under data/raw/historical/."""
    out_dir = DATA_DIR.parent / "historical" / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    trades = download_trades(symbol, start, end)
    trades.to_parquet(out_dir / "trades.parquet", index=False)
    print(f"{symbol}: {len(trades):,} trades -> {out_dir / 'trades.parquet'}")

    depth = download_book_depth(symbol, max(start, date(2023, 1, 1)), end)
    depth.to_parquet(out_dir / "book_depth.parquet", index=False)
    print(f"{symbol}: {len(depth):,} book-depth rows -> {out_dir / 'book_depth.parquet'}")


if __name__ == "__main__":
    import sys

    symbols = sys.argv[1:] or ["ALGOUSDT", "ICPUSDT", "QNTUSDT"]
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=30)
    for sym in symbols:
        backfill(sym, start, end)
