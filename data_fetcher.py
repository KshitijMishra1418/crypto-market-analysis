"""
data_fetcher.py
---------------
Fetches OHLCV crypto data from CoinGecko (free, no API key needed).
Supports BTC, ETH, SOL, BNB and any other CoinGecko coin ID.
"""

import requests
import pandas as pd
import time
import os

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

COIN_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
}

def fetch_ohlcv(symbol: str, days: int = 90, vs_currency: str = "usd") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given symbol.
    
    Args:
        symbol: e.g. 'BTC', 'ETH', or full CoinGecko ID like 'bitcoin'
        days:   number of days of history (max 365 for free tier)
        vs_currency: quote currency, default 'usd'
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    coin_id = COIN_MAP.get(symbol.upper(), symbol.lower())
    
    print(f"  Fetching {symbol} OHLCV ({days} days)...")
    
    # Fetch OHLC
    ohlc_url = f"{COINGECKO_BASE}/coins/{coin_id}/ohlc"
    ohlc_resp = requests.get(ohlc_url, params={"vs_currency": vs_currency, "days": days}, timeout=15)
    ohlc_resp.raise_for_status()
    ohlc_data = ohlc_resp.json()
    
    # Fetch volume via market_chart
    time.sleep(1.2)  # respect rate limit
    chart_url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    chart_resp = requests.get(chart_url, params={"vs_currency": vs_currency, "days": days}, timeout=15)
    chart_resp.raise_for_status()
    chart_data = chart_resp.json()
    
    # Build OHLC dataframe
    ohlc_df = pd.DataFrame(ohlc_data, columns=["timestamp", "open", "high", "low", "close"])
    ohlc_df["timestamp"] = pd.to_datetime(ohlc_df["timestamp"], unit="ms")
    ohlc_df.set_index("timestamp", inplace=True)
    
    # Build volume dataframe (daily granularity)
    vol_df = pd.DataFrame(chart_data["total_volumes"], columns=["timestamp", "volume"])
    vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
    vol_df.set_index("timestamp", inplace=True)
    
    # Resample volume to match OHLC frequency then merge
    vol_resampled = vol_df["volume"].resample("4h").mean()
    df = ohlc_df.join(vol_resampled, how="left")
    df["symbol"] = symbol.upper()
    df.dropna(inplace=True)
    
    print(f"  Got {len(df)} rows for {symbol}")
    return df


def fetch_multiple(symbols: list, days: int = 90) -> dict:
    """Fetch data for multiple symbols. Returns dict of {symbol: DataFrame}."""
    results = {}
    for sym in symbols:
        try:
            results[sym] = fetch_ohlcv(sym, days=days)
            time.sleep(1.5)
        except Exception as e:
            print(f"  Warning: Could not fetch {sym} — {e}")
    return results


def save_data(data: dict, folder: str = "data"):
    """Save each symbol's DataFrame to CSV."""
    os.makedirs(folder, exist_ok=True)
    for sym, df in data.items():
        path = os.path.join(folder, f"{sym}_ohlcv.csv")
        df.to_csv(path)
        print(f"  Saved {path}")


def load_data(symbols: list, folder: str = "data") -> dict:
    """Load saved CSVs instead of re-fetching."""
    results = {}
    for sym in symbols:
        path = os.path.join(folder, f"{sym}_ohlcv.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            results[sym] = df
            print(f"  Loaded {path}")
        else:
            print(f"  No saved data for {sym}, skipping.")
    return results


if __name__ == "__main__":
    print("=== Fetching Crypto Data ===")
    data = fetch_multiple(["BTC", "ETH", "SOL"], days=90)
    save_data(data)
    print("\nDone! Data saved to /data folder.")
    print(data["BTC"].tail())
