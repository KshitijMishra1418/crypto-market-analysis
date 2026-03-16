"""
volatility_analysis.py
-----------------------
Computes volatility regimes using:
  - Rolling standard deviation of log returns
  - ATR (Average True Range)
  - Bollinger Bands
  - Volatility regime classification (Low / Medium / High)
"""

import pandas as pd
import numpy as np


def compute_log_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add log return column."""
    df = df.copy()
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    return df


def rolling_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Rolling annualised volatility from log returns.
    Assumes 4h candles → 6 candles/day → annualise by sqrt(6*365).
    """
    df = df.copy()
    candles_per_year = 6 * 365
    df["volatility"] = df["log_return"].rolling(window).std() * np.sqrt(candles_per_year)
    return df


def atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average True Range."""
    df = df.copy()
    high_low   = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close  = (df["low"]  - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(period).mean()
    df["atr_pct"] = df["atr"] / df["close"] * 100   # ATR as % of price
    return df


def bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands + %B + bandwidth."""
    df = df.copy()
    rolling = df["close"].rolling(window)
    df["bb_mid"]   = rolling.mean()
    df["bb_upper"] = df["bb_mid"] + num_std * rolling.std()
    df["bb_lower"] = df["bb_mid"] - num_std * rolling.std()
    df["bb_pct"]   = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
    return df


def classify_regime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label each row as Low / Medium / High volatility regime
    based on percentile of rolling volatility.
    """
    df = df.copy()
    vol = df["volatility"].dropna()
    low_thresh  = vol.quantile(0.33)
    high_thresh = vol.quantile(0.66)

    def label(v):
        if pd.isna(v):       return "Unknown"
        if v <= low_thresh:  return "Low"
        if v <= high_thresh: return "Medium"
        return "High"

    df["regime"] = df["volatility"].apply(label)
    return df


def regime_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Summary stats per regime."""
    stats = (
        df.groupby("regime")
        .agg(
            count=("close", "count"),
            avg_return=("log_return", "mean"),
            avg_volatility=("volatility", "mean"),
            avg_atr_pct=("atr_pct", "mean"),
            avg_volume=("volume", "mean"),
        )
        .round(6)
    )
    stats["avg_return_pct"] = (stats["avg_return"] * 100).round(4)
    return stats


def full_volatility_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Run all volatility metrics in one call."""
    df = compute_log_returns(df)
    df = rolling_volatility(df)
    df = atr(df)
    df = bollinger_bands(df)
    df = classify_regime(df)
    return df


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_fetcher import load_data

    data = load_data(["BTC"], folder="data")
    if not data:
        print("No data found. Run data_fetcher.py first.")
    else:
        df = full_volatility_analysis(data["BTC"])
        print("\n=== Regime Distribution ===")
        print(df["regime"].value_counts())
        print("\n=== Regime Stats ===")
        print(regime_stats(df))
