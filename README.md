# Crypto Market Analysis System

A Python-based pipeline to analyse cryptocurrency market behaviour — 
volatility clustering, liquidity microstructure, and breakout detection.

Built by **Kshitij Mishra** — kshitij.info

---

## What It Does

| Module | Analysis |
|--------|----------|
| `data_fetcher.py`       | Fetches OHLCV data from CoinGecko (free, no API key) |
| `volatility_analysis.py`| Rolling volatility, ATR, Bollinger Bands, regime classification |
| `liquidity_analysis.py` | VWAP, volume z-score, spread proxy, breakout detection |
| `charts.py`             | 6 publication-quality dark-theme charts |
| `report.py`             | Structured text + CSV report |
| `main.py`               | Full pipeline runner |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run full analysis (BTC, ETH, SOL — 90 days)
python main.py

# 3. Custom coins & timeframe
python main.py --coins BTC ETH SOL BNB --days 180

# 4. Re-run without re-fetching data
python main.py --load
```

---

## Output

```
charts/
  BTC_price_bb.png              # Price + Bollinger Bands + Volume
  BTC_volatility_regime.png     # Volatility coloured by regime
  BTC_breakouts.png             # Price + breakout markers
  BTC_liquidity_heatmap.png     # Liquidity by hour & day
  BTC_regime_distribution.png   # Regime stats bar charts
  correlation_matrix.png        # Cross-coin correlation

outputs/
  analysis_report_YYYYMMDD.txt  # Full analysis report
  full_data_YYYYMMDD.csv        # Combined data CSV
  breakout_log_YYYYMMDD.csv     # All detected breakouts
```

---

## Key Concepts

**Volatility Regimes**  
Each candle is labelled Low / Medium / High based on percentile of 
rolling annualised volatility. Helps identify market stress periods.

**Breakout Detection**  
A breakout is triggered when price closes >2% beyond the 20-period 
rolling high or low. Useful for momentum signals.

**Liquidity Score**  
Composite 0–100 score combining volume z-score, spread proxy, and 
price efficiency ratio. Higher = more liquid conditions.

**Trend Persistence**  
Autocorrelation of log returns at lags 1/3/6/12 candles.  
Positive → trending market. Negative → mean-reverting market.

---

## Tech Stack

- **Python** — core language
- **Pandas / NumPy** — data manipulation
- **Matplotlib** — visualisation
- **Requests** — API calls (CoinGecko free tier)

---

## Supported Coins

`BTC` `ETH` `SOL` `BNB` `ADA` `XRP` `DOGE`  
Or pass any CoinGecko coin ID directly (e.g. `chainlink`, `avalanche-2`)
