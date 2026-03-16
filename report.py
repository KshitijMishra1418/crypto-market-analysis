"""
report.py
----------
Generates a structured analysis report:
  - Summary stats per coin
  - Regime breakdown
  - Breakout log
  - Trend persistence
  - Saves everything to /outputs folder
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime


def generate_report(data_analyzed: dict, output_dir: str = "outputs") -> str:
    """
    data_analyzed: dict of {symbol: fully-analyzed DataFrame}
    Returns path to the report text file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_lines = []

    def line(text=""):
        report_lines.append(text)

    line("=" * 65)
    line("       CRYPTO MARKET ANALYSIS REPORT")
    line(f"       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    line("=" * 65)

    for symbol, df in data_analyzed.items():
        df = df.dropna(subset=["close"])
        line()
        line(f"  ── {symbol} ─────────────────────────────────────────")
        line()

        # Price summary
        line(f"  Price Range:    ${df['close'].min():,.2f}  —  ${df['close'].max():,.2f}")
        line(f"  Current Price:  ${df['close'].iloc[-1]:,.2f}")
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        line(f"  Period Return:  {total_return:+.2f}%")
        line(f"  Data Points:    {len(df)} candles (4h)")
        line()

        # Volatility
        if "volatility" in df.columns:
            avg_vol = df["volatility"].mean()
            max_vol = df["volatility"].max()
            line(f"  Avg Volatility: {avg_vol:.2%} (annualised)")
            line(f"  Max Volatility: {max_vol:.2%}")
            line()

        # Regime breakdown
        if "regime" in df.columns:
            counts = df["regime"].value_counts()
            total  = len(df)
            line("  Regime Distribution:")
            for r in ["Low", "Medium", "High"]:
                n = counts.get(r, 0)
                line(f"    {r:<8}  {n:>4} candles  ({n/total*100:.1f}%)")
            line()

        # Breakouts
        if "breakout_type" in df.columns:
            bull = (df["breakout_type"] == "Bullish").sum()
            bear = (df["breakout_type"] == "Bearish").sum()
            line(f"  Breakouts Detected:")
            line(f"    Bullish: {bull}")
            line(f"    Bearish: {bear}")
            line()

        # Trend persistence
        if "log_return" in df.columns:
            line("  Trend Persistence (Autocorrelation):")
            for lag in [1, 3, 6, 12]:
                ac = df["log_return"].autocorr(lag=lag)
                direction = "Trending" if ac > 0.05 else ("Mean-Reverting" if ac < -0.05 else "Random")
                line(f"    Lag {lag:>2}h:  {ac:+.4f}  → {direction}")
            line()

        # Liquidity
        if "liquidity_score" in df.columns:
            avg_liq = df["liquidity_score"].mean()
            line(f"  Avg Liquidity Score: {avg_liq:.1f} / 100")
            peak_hour = df.groupby(df.index.hour)["liquidity_score"].mean().idxmax()
            line(f"  Most Liquid Hour:    {peak_hour:02d}:00 UTC")
            line()

        # VWAP
        if "vwap" in df.columns:
            last_close = df["close"].iloc[-1]
            last_vwap  = df["vwap"].iloc[-1]
            rel = (last_close - last_vwap) / last_vwap * 100
            line(f"  Price vs VWAP:   {rel:+.2f}%  ({'Above' if rel >= 0 else 'Below'})")
            line()

    line("=" * 65)
    line("  End of Report")
    line("=" * 65)

    # Save report
    report_path = os.path.join(output_dir, f"analysis_report_{timestamp}.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    # Also save combined CSV
    all_dfs = []
    for symbol, df in data_analyzed.items():
        df["symbol"] = symbol
        all_dfs.append(df)

    combined = pd.concat(all_dfs)
    csv_path = os.path.join(output_dir, f"full_data_{timestamp}.csv")
    combined.to_csv(csv_path)

    # Breakout log CSV
    breakouts = combined[combined.get("breakout_type", pd.Series("None", index=combined.index)) != "None"].copy() if "breakout_type" in combined.columns else pd.DataFrame()
    if not breakouts.empty:
        bl_path = os.path.join(output_dir, f"breakout_log_{timestamp}.csv")
        breakouts[["symbol","close","breakout_type","volume","volatility"]].to_csv(bl_path)

    print("\n".join(report_lines))
    print(f"\nReport saved: {report_path}")
    print(f"Data CSV saved: {csv_path}")
    return report_path
