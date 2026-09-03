# Algorithmic-Crypto-Analysis-

Studies on crypto ideas, anomalies, and crypto related ideas.

## Current focus: alpha in less-liquid coins

First study: whether real orderflow (order book imbalance, trade-print
patterns) shows exploitable microstructure inefficiency in mid-cap coins
that are still listed on major exchanges but trade much thinner, relative
to their size, than BTC/ETH/SOL.

Starting universe: **ALGO, ICP, QNT** — picked by screening CoinGecko
market data for coins ranked ~30-120 by market cap with the lowest
24h-volume / market-cap ratios, excluding stablecoins/RWA/wrapped tokens
and anything with too little real volume to have a meaningful book.

## Data sourcing

- **CoinGecko API** (`src/data_sources/coingecko_screener.py`) — aggregated
  market data only (price, volume, market cap). Used to screen and rank
  the coin universe. Requires `COINGECKO_API_KEY` in `.env`.
- **Coinbase Exchange public WebSocket feed**
  (`src/data_sources/coinbase_orderflow.py`) — live, full-depth orderflow
  going forward: full order book (`level2_batch`, all price levels, not
  just top-N) and every individual trade (`matches`). Free, no API key,
  not geo-restricted in the US. (Binance.com's equivalent feed returns
  HTTP 451 for US IPs — Coinbase is the free alternative.) Only covers
  data from whenever the capture is actually running.
- **Binance public data archive** (`src/data_sources/binance_vision.py`) —
  free bulk *historical* orderflow, going back years, no API key. This
  archive (`data.binance.vision`) is static file storage, not the
  geo-blocked live API, so it works from the US. Two datasets:
  - spot daily trade tape (tick-by-tick, with side) back to each symbol's
    listing date
  - futures `bookDepth`: order-book depth at ±1-5% from mid-price,
    sampled ~every 30s, back to 2023-01-01 (futures market, used as a
    liquidity proxy for the same underlying asset — there's no free
    historical *spot* order-book depth anywhere)

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate on mac/linux
pip install -r requirements.txt
cp .env.example .env  # fill in COINGECKO_API_KEY
```

## Usage

```bash
# rank candidate coins by thinness of relative liquidity
python -m src.data_sources.coingecko_screener

# backfill historical trades + book depth for the starting universe
python -m src.data_sources.binance_vision ALGOUSDT ICPUSDT QNTUSDT

# capture live order book + trade data going forward
python -m src.data_sources.coinbase_orderflow ALGO ICP QNT
```

Data lands in `data/raw/<PRODUCT>/<date>.jsonl` (live capture) and
`data/historical/<SYMBOL>/*.parquet` (backfill) — both gitignored,
regenerable, not meant to be committed.


Data can also be sourced easily holding it will be the trouble need approximately 500 gbs to hold around 3 years of orderbook and order flow tick level data for ALGO coin. 
