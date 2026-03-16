"""
main.py
--------
Full pipeline runner for Crypto Market Analysis System.

Usage:
    python main.py                        # fetch fresh data + full analysis
    python main.py --coins BTC ETH SOL   # specify coins
    python main.py --days 180            # change history window
    python main.py --load                # skip fetch, use saved CSV data

Output:
    charts/  — all PNG charts
    outputs/ — report .txt and .csv files
"""

import argparse
import os
import sys

from data_fetcher      import fetch_multiple, save_data, load_data
from volatility_analysis import full_volatility_analysis, regime_stats
from liquidity_analysis  import full_liquidity_analysis, trend_persistence
from charts            import (chart_price_bb, chart_volatility_regime,
                                chart_breakouts, chart_liquidity_heatmap,
                                chart_correlation, chart_regime_distribution)
from report            import generate_report


def main():
    parser = argparse.ArgumentParser(description="Crypto Market Analysis System")
    parser.add_argument("--coins", nargs="+", default=["BTC", "ETH", "SOL"],
                        help="Coin symbols to analyse")
    parser.add_argument("--days",  type=int, default=90,
                        help="Days of history to fetch (default: 90)")
    parser.add_argument("--load",  action="store_true",
                        help="Load from saved CSVs instead of fetching new data")
    args = parser.parse_args()

    os.makedirs("charts",  exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("data",    exist_ok=True)

    # ── Step 1: Fetch or Load Data ────────────────────────────────────────
    print("\n" + "="*55)
    print("  CRYPTO MARKET ANALYSIS SYSTEM")
    print("="*55)

    if args.load:
        print("\n[1/4] Loading saved data...")
        raw_data = load_data(args.coins, folder="data")
    else:
        print(f"\n[1/4] Fetching data for {args.coins} ({args.days} days)...")
        raw_data = fetch_multiple(args.coins, days=args.days)
        save_data(raw_data, folder="data")

    if not raw_data:
        print("No data available. Check your internet connection and try again.")
        sys.exit(1)

    # ── Step 2: Run Analysis ──────────────────────────────────────────────
    print("\n[2/4] Running analysis...")
    analyzed = {}
    for sym, df in raw_data.items():
        print(f"  Analysing {sym}...")
        df = full_volatility_analysis(df)
        df = full_liquidity_analysis(df)
        analyzed[sym] = df

        print(f"    Regime stats:")
        stats = regime_stats(df)
        for regime, row in stats.iterrows():
            print(f"      {regime:<8}: {int(row['count'])} candles, "
                  f"avg vol {row['avg_volatility']:.2%}")

        print(f"    Trend persistence:")
        tp = trend_persistence(df)
        for k, v in tp.items():
            print(f"      {k}: {v:.4f}")

    # ── Step 3: Generate Charts ───────────────────────────────────────────
    print("\n[3/4] Generating charts...")
    for sym, df in analyzed.items():
        chart_price_bb(df, sym)
        chart_volatility_regime(df, sym)
        chart_breakouts(df, sym)
        chart_liquidity_heatmap(df, sym)
        chart_regime_distribution(df, sym)

    if len(analyzed) >= 2:
        chart_correlation(analyzed)

    # ── Step 4: Generate Report ───────────────────────────────────────────
    print("\n[4/4] Generating report...")
    generate_report(analyzed)

    print("\n" + "="*55)
    print("  ANALYSIS COMPLETE")
    print(f"  Charts:  /charts/ ({len(os.listdir('charts'))} files)")
    print(f"  Reports: /outputs/ ({len(os.listdir('outputs'))} files)")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
