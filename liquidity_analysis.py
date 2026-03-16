"""
liquidity_analysis.py
----------------------
Analyses market liquidity and microstructure signals:
  - Volume profile & VWAP
  - Volume z-score (liquidity spikes)
  - Price efficiency ratio
  - Spread proxy (high-low range as % of close)
  - Trend persistence using autocorrelation
  - Breakout detection
"""

import pandas as pd
import numpy as np


def vwap(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Rolling VWAP."""
    df = df.copy()
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["typical_price"] = typical_price
    df["vwap"] = (
        (typical_price * df["volume"]).rolling(window).sum()
        / df["volume"].rolling(window).sum()
    )
    df["price_vs_vwap"] = (df["close"] - df["vwap"]) / df["vwap"] * 100
    return df


def volume_zscore(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Z-score of volume to detect liquidity spikes."""
    df = df.copy()
    rolling = df["volume"].rolling(window)
    df["vol_zscore"] = (df["volume"] - rolling.mean()) / rolling.std()
    df["vol_spike"] = df["vol_zscore"] > 2.0   # True = unusual volume
    return df


def spread_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    High-Low spread as % of close — proxy for bid-ask spread
    in the absence of order book data.
    """
    df = df.copy()
    df["spread_pct"] = (df["high"] - df["low"]) / df["close"] * 100
    df["spread_ma"]  = df["spread_pct"].rolling(20).mean()
    return df


def price_efficiency(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Price Efficiency Ratio = |net move| / sum(|individual moves|)
    1.0 = perfect trend, 0.0 = random walk.
    """
    df = df.copy()
    net   = (df["close"] - df["close"].shift(window)).abs()
    path  = df["close"].diff().abs().rolling(window).sum()
    df["efficiency_ratio"] = net / path
    return df


def trend_persistence(df: pd.DataFrame, lags: list = [1, 3, 6]) -> dict:
    """
    Autocorrelation of log returns at given lags.
    Positive = trend-following, Negative = mean-reverting.
    """
    if "log_return" not in df.columns:
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    results = {}
    for lag in lags:
        results[f"autocorr_lag{lag}"] = df["log_return"].autocorr(lag=lag)
    return results


def detect_breakouts(df: pd.DataFrame, lookback: int = 20, threshold: float = 0.02) -> pd.DataFrame:
    """
    Detect price breakouts above recent highs or below recent lows.
    threshold = 2% move beyond the rolling high/low.
    """
    df = df.copy()
    df["rolling_high"] = df["high"].rolling(lookback).max().shift(1)
    df["rolling_low"]  = df["low"].rolling(lookback).min().shift(1)
    df["breakout_up"]   = df["close"] > df["rolling_high"] * (1 + threshold)
    df["breakout_down"] = df["close"] < df["rolling_low"]  * (1 - threshold)
    df["breakout_type"] = "None"
    df.loc[df["breakout_up"],   "breakout_type"] = "Bullish"
    df.loc[df["breakout_down"], "breakout_type"] = "Bearish"
    return df


def liquidity_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Composite liquidity score 0–100.
    Higher = more liquid (tighter spread, high volume, efficient price).
    """
    df = df.copy()

    # Normalise components to 0-1 range
    def norm(s, invert=False):
        mn, mx = s.min(), s.max()
        if mx == mn:
            return pd.Series(0.5, index=s.index)
        n = (s - mn) / (mx - mn)
        return 1 - n if invert else n

    vol_score    = norm(df.get("vol_zscore", pd.Series(0, index=df.index)).clip(lower=0))
    spread_score = norm(df.get("spread_pct", pd.Series(1, index=df.index)), invert=True)
    eff_score    = norm(df.get("efficiency_ratio", pd.Series(0.5, index=df.index)))

    df["liquidity_score"] = ((vol_score + spread_score + eff_score) / 3 * 100).round(1)
    return df


def full_liquidity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Run all liquidity metrics in one call."""
    df = vwap(df)
    df = volume_zscore(df)
    df = spread_proxy(df)
    df = price_efficiency(df)
    df = detect_breakouts(df)
    df = liquidity_score(df)
    return df


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_fetcher import load_data

    data = load_data(["BTC"], folder="data")
    if not data:
        print("No data found. Run data_fetcher.py first.")
    else:
        df = full_liquidity_analysis(data["BTC"])
        persistence = trend_persistence(df)
        print("\n=== Trend Persistence (Autocorrelation) ===")
        for k, v in persistence.items():
            print(f"  {k}: {v:.4f}")
        print("\n=== Breakout Summary ===")
        print(df["breakout_type"].value_counts())
        print("\n=== Avg Liquidity Score by Hour ===")
        print(df.groupby(df.index.hour)["liquidity_score"].mean().round(1))
