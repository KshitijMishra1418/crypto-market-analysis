"""
charts.py
----------
Generates all analysis charts:
  1. Price + Volume + Bollinger Bands
  2. Volatility Regime Timeline
  3. Breakout Map
  4. Liquidity Score Heatmap (by hour)
  5. Multi-coin Correlation Matrix
  6. Volatility Regime Distribution (bar)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import os

STYLE = {
    "bg":       "#0d1117",
    "surface":  "#161b22",
    "accent":   "#58a6ff",
    "green":    "#3fb950",
    "red":      "#f85149",
    "yellow":   "#d29922",
    "purple":   "#bc8cff",
    "text":     "#e6edf3",
    "muted":    "#8b949e",
    "grid":     "#21262d",
}

def _apply_dark(fig, axes):
    fig.patch.set_facecolor(STYLE["bg"])
    for ax in (axes if hasattr(axes, '__iter__') else [axes]):
        ax.set_facecolor(STYLE["surface"])
        ax.tick_params(colors=STYLE["muted"], labelsize=9)
        ax.xaxis.label.set_color(STYLE["muted"])
        ax.yaxis.label.set_color(STYLE["muted"])
        ax.title.set_color(STYLE["text"])
        for spine in ax.spines.values():
            spine.set_color(STYLE["grid"])
        ax.grid(color=STYLE["grid"], linewidth=0.5, linestyle="--", alpha=0.7)


def chart_price_bb(df: pd.DataFrame, symbol: str, save_dir: str = "charts"):
    """Price chart with Bollinger Bands and volume bars."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [3, 1]})
    _apply_dark(fig, [ax1, ax2])
    fig.suptitle(f"{symbol} — Price & Bollinger Bands", color=STYLE["text"], fontsize=14, y=0.98)

    ax1.plot(df.index, df["close"],    color=STYLE["accent"],  lw=1.5, label="Close")
    ax1.plot(df.index, df["bb_upper"], color=STYLE["muted"],   lw=0.8, ls="--", label="BB Upper")
    ax1.plot(df.index, df["bb_lower"], color=STYLE["muted"],   lw=0.8, ls="--", label="BB Lower")
    ax1.plot(df.index, df["bb_mid"],   color=STYLE["yellow"],  lw=0.8, ls=":",  label="BB Mid")
    ax1.fill_between(df.index, df["bb_lower"], df["bb_upper"],
                     alpha=0.06, color=STYLE["accent"])
    if "vwap" in df.columns:
        ax1.plot(df.index, df["vwap"], color=STYLE["purple"], lw=1.0, ls="-.", label="VWAP")

    ax1.set_ylabel("Price (USD)")
    ax1.legend(loc="upper left", fontsize=8, facecolor=STYLE["surface"], labelcolor=STYLE["text"])

    colors = [STYLE["green"] if r >= 0 else STYLE["red"]
              for r in df["log_return"].fillna(0)]
    ax2.bar(df.index, df["volume"], color=colors, alpha=0.7, width=0.12)
    ax2.set_ylabel("Volume")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)

    plt.tight_layout()
    path = os.path.join(save_dir, f"{symbol}_price_bb.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart_volatility_regime(df: pd.DataFrame, symbol: str, save_dir: str = "charts"):
    """Volatility over time coloured by regime."""
    fig, ax = plt.subplots(figsize=(14, 5))
    _apply_dark(fig, ax)
    ax.set_title(f"{symbol} — Volatility Regime", color=STYLE["text"], fontsize=13)

    regime_colors = {"Low": STYLE["green"], "Medium": STYLE["yellow"],
                     "High": STYLE["red"],  "Unknown": STYLE["muted"]}

    for regime, color in regime_colors.items():
        mask = df["regime"] == regime
        ax.fill_between(df.index, 0, df["volatility"].where(mask),
                        color=color, alpha=0.6, label=regime)

    ax.plot(df.index, df["volatility"], color=STYLE["text"], lw=0.8, alpha=0.5)
    ax.set_ylabel("Annualised Volatility")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    ax.legend(loc="upper right", fontsize=9, facecolor=STYLE["surface"], labelcolor=STYLE["text"])

    plt.tight_layout()
    path = os.path.join(save_dir, f"{symbol}_volatility_regime.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart_breakouts(df: pd.DataFrame, symbol: str, save_dir: str = "charts"):
    """Price chart with breakout markers."""
    fig, ax = plt.subplots(figsize=(14, 6))
    _apply_dark(fig, ax)
    ax.set_title(f"{symbol} — Breakout Detection", color=STYLE["text"], fontsize=13)

    ax.plot(df.index, df["close"],        color=STYLE["accent"], lw=1.2, label="Close", zorder=2)
    ax.plot(df.index, df["rolling_high"], color=STYLE["green"],  lw=0.7, ls="--", alpha=0.6, label="Rolling High")
    ax.plot(df.index, df["rolling_low"],  color=STYLE["red"],    lw=0.7, ls="--", alpha=0.6, label="Rolling Low")

    bull = df[df["breakout_type"] == "Bullish"]
    bear = df[df["breakout_type"] == "Bearish"]
    ax.scatter(bull.index, bull["close"], color=STYLE["green"], marker="^", s=80, zorder=5, label=f"Bullish Breakout ({len(bull)})")
    ax.scatter(bear.index, bear["close"], color=STYLE["red"],   marker="v", s=80, zorder=5, label=f"Bearish Breakout ({len(bear)})")

    ax.set_ylabel("Price (USD)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    ax.legend(loc="upper left", fontsize=8, facecolor=STYLE["surface"], labelcolor=STYLE["text"])

    plt.tight_layout()
    path = os.path.join(save_dir, f"{symbol}_breakouts.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart_liquidity_heatmap(df: pd.DataFrame, symbol: str, save_dir: str = "charts"):
    """Liquidity score heatmap: hour of day vs day of week."""
    df2 = df.copy()
    df2["hour"] = df2.index.hour
    df2["dow"]  = df2.index.day_name()

    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = df2.pivot_table(values="liquidity_score", index="dow", columns="hour", aggfunc="mean")
    pivot = pivot.reindex([d for d in order if d in pivot.index])

    fig, ax = plt.subplots(figsize=(16, 5))
    _apply_dark(fig, ax)
    ax.set_title(f"{symbol} — Avg Liquidity Score by Hour & Day", color=STYLE["text"], fontsize=13)

    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}h" for h in range(24)], fontsize=7, color=STYLE["muted"])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9, color=STYLE["muted"])
    cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cbar.ax.yaxis.set_tick_params(color=STYLE["muted"], labelcolor=STYLE["muted"])

    plt.tight_layout()
    path = os.path.join(save_dir, f"{symbol}_liquidity_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart_correlation(data: dict, save_dir: str = "charts"):
    """Correlation matrix of log returns across coins."""
    returns = {}
    for sym, df in data.items():
        if "log_return" in df.columns:
            returns[sym] = df["log_return"]

    if len(returns) < 2:
        print("  Need at least 2 coins for correlation chart.")
        return

    corr = pd.DataFrame(returns).corr()
    fig, ax = plt.subplots(figsize=(8, 7))
    _apply_dark(fig, ax)
    ax.set_title("Coin Correlation Matrix (Log Returns)", color=STYLE["text"], fontsize=13)

    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ticks = range(len(corr.columns))
    ax.set_xticks(ticks); ax.set_yticks(ticks)
    ax.set_xticklabels(corr.columns, color=STYLE["text"], fontsize=11)
    ax.set_yticklabels(corr.columns, color=STYLE["text"], fontsize=11)

    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=11, color="white" if abs(corr.iloc[i, j]) > 0.5 else STYLE["bg"])

    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.yaxis.set_tick_params(color=STYLE["muted"], labelcolor=STYLE["muted"])
    plt.tight_layout()
    path = os.path.join(save_dir, "correlation_matrix.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path


def chart_regime_distribution(df: pd.DataFrame, symbol: str, save_dir: str = "charts"):
    """Bar chart of regime distribution + avg return per regime."""
    counts  = df["regime"].value_counts().reindex(["Low","Medium","High"]).fillna(0)
    avg_ret = df.groupby("regime")["log_return"].mean().reindex(["Low","Medium","High"]).fillna(0) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    _apply_dark(fig, [ax1, ax2])
    fig.suptitle(f"{symbol} — Regime Analysis", color=STYLE["text"], fontsize=13)

    colors = [STYLE["green"], STYLE["yellow"], STYLE["red"]]
    ax1.bar(counts.index, counts.values, color=colors, alpha=0.85, width=0.5)
    ax1.set_title("Regime Distribution", color=STYLE["text"])
    ax1.set_ylabel("# Candles", color=STYLE["muted"])
    for i, v in enumerate(counts.values):
        ax1.text(i, v + 1, str(int(v)), ha="center", color=STYLE["text"], fontsize=10)

    bar_colors = [STYLE["green"] if v >= 0 else STYLE["red"] for v in avg_ret.values]
    ax2.bar(avg_ret.index, avg_ret.values, color=bar_colors, alpha=0.85, width=0.5)
    ax2.axhline(0, color=STYLE["muted"], lw=0.8)
    ax2.set_title("Avg Return per Regime (%)", color=STYLE["text"])
    ax2.set_ylabel("Avg Log Return (%)", color=STYLE["muted"])
    for i, v in enumerate(avg_ret.values):
        ax2.text(i, v + (0.0001 if v >= 0 else -0.0002), f"{v:.4f}%",
                 ha="center", color=STYLE["text"], fontsize=9)

    plt.tight_layout()
    path = os.path.join(save_dir, f"{symbol}_regime_distribution.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=STYLE["bg"])
    plt.close()
    print(f"  Saved: {path}")
    return path
