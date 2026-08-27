"""
Free, no-API-key orderflow capture from Coinbase Exchange's public
WebSocket feed (not geo-restricted in the US, unlike Binance.com):
  - level2_batch : order book snapshot + incremental diffs
  - matches      : every executed trade (price, size, side)

Writes raw messages to newline-delimited JSON, one file per product per day,
under data/raw/. This is capture only - no signal logic here, that belongs
in research/ once there's raw data to look at.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import websockets

from src.config import COINBASE_WS_URL, DATA_DIR


def _out_path(product_id: str) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_dir = DATA_DIR / product_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{day}.jsonl"


async def capture(product_ids: list[str]) -> None:
    subscribe_msg = {
        "type": "subscribe",
        "product_ids": product_ids,
        "channels": ["level2_batch", "matches"],
    }

    files = {pid: open(_out_path(pid), "a", buffering=1) for pid in product_ids}
    try:
        async with websockets.connect(COINBASE_WS_URL) as ws:
            await ws.send(json.dumps(subscribe_msg))
            print(f"subscribed: {product_ids}")
            async for raw in ws:
                msg = json.loads(raw)
                pid = msg.get("product_id")
                if pid not in files:
                    continue
                record = {"recv_ts": datetime.now(timezone.utc).isoformat(), **msg}
                files[pid].write(json.dumps(record) + "\n")
    finally:
        for f in files.values():
            f.close()


if __name__ == "__main__":
    syms = sys.argv[1:] or ["ALGO", "ICP", "QNT"]
    products = [s.upper() + "-USD" if "-" not in s else s.upper() for s in syms]
    print(f"capturing orderflow for: {products} (ctrl+c to stop)")
    try:
        asyncio.run(capture(products))
    except KeyboardInterrupt:
        pass
