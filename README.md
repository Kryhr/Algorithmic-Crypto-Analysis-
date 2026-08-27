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
  (`src/data_sources/coinbase_orderflow.py`) — the actual orderflow:
  live order book (`level2_batch`) and trade prints (`matches`). Free,
  no API key, not geo-restricted in the US. (Binance.com's equivalent
  feed returns HTTP 451 for US IPs — Coinbase is the free alternative.)

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

# capture live order book + trade data for the starting universe
python -m src.data_sources.coinbase_orderflow ALGO ICP QNT
```

Captured data lands in `data/raw/<PRODUCT>/<date>.jsonl` (gitignored —
regenerable, not meant to be committed).
