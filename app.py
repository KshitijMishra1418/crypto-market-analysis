"""
app.py
-------
Streamlit web app for Crypto Market Analysis System.
Deploy free at share.streamlit.io
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time

st.set_page_config(
    page_title="Crypto Market Analysis",
    page_icon="📈",
    layout="wide"
)

# ── Inline imports with error handling ──────────────────────────────────────
try:
    from data_fetcher import fetch_multiple, load_data, save_data
    from volatility_analysis import full_volatility_analysis, regime_stats
    from liquidity_analysis import full_liquidity_analysis, trend_persistence
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0d1117; }
    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #58a6ff; }
    .metric-label { font-size: 13px; color: #8b949e; margin-top: 4px; }
    .regime-high   { color: #f85149; font-weight: bold; }
    .regime-medium { color: #d29922; font-weight: bold; }
    .regime-low    { color: #3fb950; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

STYLE = {
    "bg":      "#0d1117",
    "surface": "#161b22",
    "accent":  "#58a6ff",
    "green":   "#3fb950",
    "red":     "#f85149",
    "yellow":  "#d29922",
    "purple":  "#bc8cff",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
    "grid":    "#21262d",
}

def apply_dark(fig, axes):
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

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📈 Crypto Market Analysis System")
st.markdown("*Volatility clustering · Liquidity microstructure · Breakout detection*")
st.markdown("---")

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    coins = st.multiselect(
        "Select Coins",
        ["BTC", "ETH", "SOL", "BNB", "ADA", "XRP", "DOGE"],
        default=["BTC", "ETH"]
    )
    days = st.slider("Days of History", min_value=30, max_value=180, value=90, step=10)
    run_btn = st.button("🚀 Run Analysis", use_container_width=True)

    st.markdown("---")
    st.markdown("**Built by [Kshitij Mishra](https://kshitij.info)**")
    st.markdown("📂 [GitHub Repo](https://github.com/KshitijMishra1418/crypto-market-analysis)")

# ── Main content ─────────────────────────────────────────────────────────────
if not run_btn:
    st.info("👈 Select coins and click **Run Analysis** to start.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📊 Volatility Analysis
        - Rolling annualised volatility
        - ATR & Bollinger Bands
        - Low / Medium / High regime classification
        """)
    with col2:
        st.markdown("""
        ### 💧 Liquidity Analysis
        - VWAP & volume z-score
        - Spread proxy & price efficiency
        - Composite liquidity score
        """)
    with col3:
        st.markdown("""
        ### 🎯 Breakout Detection
        - Rolling high/low breakouts
        - Trend persistence (autocorrelation)
        - Bullish & bearish signals
        """)

else:
    if not coins:
        st.warning("Please select at least one coin.")
        st.stop()

    # Fetch data
    with st.spinner(f"Fetching live data for {coins}..."):
        try:
            raw_data = fetch_multiple(coins, days=days)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    if not raw_data:
        st.error("No data returned. Try again in a moment (API rate limit).")
        st.stop()

    # Run analysis
    with st.spinner("Running analysis..."):
        analyzed = {}
        for sym, df in raw_data.items():
            df = full_volatility_analysis(df)
            df = full_liquidity_analysis(df)
            analyzed[sym] = df

    st.success(f"Analysis complete for {list(analyzed.keys())}!")
    st.markdown("---")

    # ── Per coin tabs ─────────────────────────────────────────────────────
    tabs = st.tabs([f"📊 {sym}" for sym in analyzed.keys()] +
                   (["🔗 Correlation"] if len(analyzed) >= 2 else []))

    for i, (sym, df) in enumerate(analyzed.items()):
        with tabs[i]:

            # Metric cards
            last_price   = df["close"].iloc[-1]
            total_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
            avg_vol      = df["volatility"].mean() * 100 if "volatility" in df.columns else 0
            liq_score    = df["liquidity_score"].mean() if "liquidity_score" in df.columns else 0
            current_regime = df["regime"].iloc[-1] if "regime" in df.columns else "Unknown"
            bull_breaks  = (df["breakout_type"] == "Bullish").sum() if "breakout_type" in df.columns else 0
            bear_breaks  = (df["breakout_type"] == "Bearish").sum() if "breakout_type" in df.columns else 0

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Current Price",   f"${last_price:,.2f}")
            col2.metric("Period Return",   f"{total_return:+.2f}%")
            col3.metric("Avg Volatility",  f"{avg_vol:.1f}%")
            col4.metric("Liquidity Score", f"{liq_score:.1f}/100")
            col5.metric("Current Regime",  current_regime)

            st.markdown("---")

            # ── Chart 1: Price + BB ───────────────────────────────────────
            st.subheader("Price + Bollinger Bands + Volume")
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True,
                                            gridspec_kw={"height_ratios": [3, 1]})
            apply_dark(fig, [ax1, ax2])
            ax1.plot(df.index, df["close"],    color=STYLE["accent"], lw=1.5, label="Close")
            ax1.plot(df.index, df["bb_upper"], color=STYLE["muted"],  lw=0.8, ls="--", label="BB Upper")
            ax1.plot(df.index, df["bb_lower"], color=STYLE["muted"],  lw=0.8, ls="--", label="BB Lower")
            ax1.plot(df.index, df["bb_mid"],   color=STYLE["yellow"], lw=0.8, ls=":",  label="BB Mid")
            ax1.fill_between(df.index, df["bb_lower"], df["bb_upper"], alpha=0.06, color=STYLE["accent"])
            if "vwap" in df.columns:
                ax1.plot(df.index, df["vwap"], color=STYLE["purple"], lw=1.0, ls="-.", label="VWAP")
            ax1.set_ylabel("Price (USD)", color=STYLE["muted"])
            ax1.legend(loc="upper left", fontsize=8, facecolor=STYLE["surface"], labelcolor=STYLE["text"])
            colors = [STYLE["green"] if r >= 0 else STYLE["red"] for r in df["log_return"].fillna(0)]
            ax2.bar(df.index, df["volume"], color=colors, alpha=0.7, width=0.12)
            ax2.set_ylabel("Volume", color=STYLE["muted"])
            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            fig.autofmt_xdate(rotation=30)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # ── Chart 2: Volatility Regime ────────────────────────────────
            st.subheader("Volatility Regime Timeline")
            fig, ax = plt.subplots(figsize=(14, 4))
            apply_dark(fig, ax)
            regime_colors = {"Low": STYLE["green"], "Medium": STYLE["yellow"],
                             "High": STYLE["red"],  "Unknown": STYLE["muted"]}
            for regime, color in regime_colors.items():
                mask = df["regime"] == regime
                ax.fill_between(df.index, 0, df["volatility"].where(mask), color=color, alpha=0.6, label=regime)
            ax.plot(df.index, df["volatility"], color=STYLE["text"], lw=0.8, alpha=0.5)
            ax.set_ylabel("Annualised Volatility", color=STYLE["muted"])
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            ax.legend(loc="upper right", fontsize=9, facecolor=STYLE["surface"], labelcolor=STYLE["text"])
            fig.autofmt_xdate(rotation=30)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            col1, col2 = st.columns(2)

            # ── Chart 3: Breakouts ────────────────────────────────────────
            with col1:
                st.subheader("Breakout Detection")
                fig, ax = plt.subplots(figsize=(8, 4))
                apply_dark(fig, ax)
                ax.plot(df.index, df["close"], color=STYLE["accent"], lw=1.2)
                ax.plot(df.index, df["rolling_high"], color=STYLE["green"], lw=0.7, ls="--", alpha=0.6)
                ax.plot(df.index, df["rolling_low"],  color=STYLE["red"],   lw=0.7, ls="--", alpha=0.6)
                bull = df[df["breakout_type"] == "Bullish"]
                bear = df[df["breakout_type"] == "Bearish"]
                ax.scatter(bull.index, bull["close"], color=STYLE["green"], marker="^", s=60, zorder=5, label=f"Bullish ({len(bull)})")
                ax.scatter(bear.index, bear["close"], color=STYLE["red"],   marker="v", s=60, zorder=5, label=f"Bearish ({len(bear)})")
                ax.legend(fontsize=8, facecolor=STYLE["surface"], labelcolor=STYLE["text"])
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
                fig.autofmt_xdate(rotation=30)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # ── Chart 4: Regime Distribution ──────────────────────────────
            with col2:
                st.subheader("Regime Distribution")
                counts  = df["regime"].value_counts().reindex(["Low","Medium","High"]).fillna(0)
                fig, ax = plt.subplots(figsize=(8, 4))
                apply_dark(fig, ax)
                colors  = [STYLE["green"], STYLE["yellow"], STYLE["red"]]
                ax.bar(counts.index, counts.values, color=colors, alpha=0.85, width=0.5)
                for idx, v in enumerate(counts.values):
                    ax.text(idx, v + 0.5, str(int(v)), ha="center", color=STYLE["text"], fontsize=11)
                ax.set_ylabel("# Candles", color=STYLE["muted"])
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # ── Trend Persistence ─────────────────────────────────────────
            st.subheader("Trend Persistence (Autocorrelation)")
            tp = trend_persistence(df, lags=[1, 3, 6, 12])
            tp_col1, tp_col2, tp_col3, tp_col4 = st.columns(4)
            for col, (k, v) in zip([tp_col1, tp_col2, tp_col3, tp_col4], tp.items()):
                direction = "Trending 📈" if v > 0.05 else ("Mean-Rev 🔄" if v < -0.05 else "Random ↔️")
                col.metric(k.replace("autocorr_", "Lag "), f"{v:.4f}", direction)

            # ── Regime Stats Table ────────────────────────────────────────
            st.subheader("Regime Summary Table")
            stats = regime_stats(df)[["count","avg_return_pct","avg_volatility","avg_volume"]].copy()
            stats.columns = ["Candles", "Avg Return %", "Avg Volatility", "Avg Volume"]
            stats["Avg Volatility"] = (stats["Avg Volatility"] * 100).round(2).astype(str) + "%"
            st.dataframe(stats, use_container_width=True)

    # ── Correlation tab ───────────────────────────────────────────────────
    if len(analyzed) >= 2:
        with tabs[-1]:
            st.subheader("Cross-Coin Correlation Matrix")
            returns = {sym: df["log_return"] for sym, df in analyzed.items() if "log_return" in df.columns}
            corr = pd.DataFrame(returns).corr()
            fig, ax = plt.subplots(figsize=(8, 6))
            apply_dark(fig, ax)
            im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr.columns))); ax.set_yticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, color=STYLE["text"], fontsize=12)
            ax.set_yticklabels(corr.columns, color=STYLE["text"], fontsize=12)
            for i in range(len(corr)):
                for j in range(len(corr)):
                    ax.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center",
                            fontsize=12, color="white" if abs(corr.iloc[i,j]) > 0.5 else "#0d1117")
            plt.colorbar(im, ax=ax)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.info("Correlation > 0.7 means coins move together. < 0.3 means they move independently.")

