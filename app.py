"""JSM RiskVault - Streamlit app (PSX stock risk score + PDF report).
Chalane ke liye:  streamlit run app.py
"""
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

BRAND = "JSM RiskVault"
MAX_TICKERS = 20
DISCLAIMER = ("This report is an informational, data-based tool built from past prices. "
              "It is NOT investment advice and does not predict future returns. Please do "
              "your own research or consult a licensed advisor before investing.")


# ---------- DATA ----------
def normalize(t):
    t = t.strip().upper()
    if not t:
        return None
    return t if "." in t else t + ".KA"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_close(symbol):
    """Asli price data. Na mile to None (random number kabhi nahi)."""
    try:
        df = yf.Ticker(symbol).history(period="1y", auto_adjust=True)
        close = df["Close"].dropna()
        return close if len(close) >= 60 else None
    except Exception:
        return None


# ---------- METRICS + SCORE ----------
def compute_metrics(close):
    rets = close.pct_change().dropna()
    return {
        "price": float(close.iloc[-1]),
        "change_1d": float(rets.iloc[-1] * 100),
        "vol": float(rets.std() * np.sqrt(250)),
        "max_dd": float(((close / close.cummax()) - 1).min()),
        "ret_3m": float(close.iloc[-1] / close.iloc[-63] - 1) if len(close) > 63 else float("nan"),
        "last_date": close.index[-1].strftime("%Y-%m-%d"),
        "days": len(close),
    }


def risk_score(m):
    """0-100, zyada = zyada risk. 40% volatility + 40% max drawdown + 20% negative 3M trend."""
    vol_s = min(m["vol"] / 0.60, 1) * 100
    dd_s = min(abs(m["max_dd"]) / 0.50, 1) * 100
    r3 = m["ret_3m"]
    trend_s = 0 if np.isnan(r3) else min(max(-r3, 0) / 0.30, 1) * 100
    return round(0.4 * vol_s + 0.4 * dd_s + 0.2 * trend_s), (round(vol_s), round(dd_s), round(trend_s))


def level(score):
    if score < 35:
        return "GREEN", colors.HexColor("#2E9E4F")
    if score < 65:
        return "YELLOW", colors.HexColor("#E0A800")
    return "RED", colors.HexColor("#D32F2F")


def chart_png(close, name):
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.plot(close.index, close.values, linewidth=1.6, color="#0A5FB4")
    ax.fill_between(close.index, close.values, close.min(), alpha=0.10, color="#0A5FB4")
    ax.set_title(f"{name} - 1 year price (Rs.)", fontsize=10)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)
    return buf


def analyze(tickers, progress=None):
    results, failed = [], []
    for i, sym in enumerate(tickers):
        name = sym.replace(".KA", "")
        close = fetch_close(sym)
        if close is None:
            failed.append(name)
        else:
            m = compute_metrics(close)
            score, parts = risk_score(m)
            lvl, col = level(score)
            results.append({"name": name, "m": m, "score": score, "parts": parts,
                            "level": lvl, "color": col, "close": close})
        if progress:
            progress.progress((i + 1) / len(tickers))
    results.sort(key=lambda r: r["score"], reverse=True)
    return results, failed


# ---------- PDF (memory me, file disk pe nahi) ----------
def build_pdf(results, failed):
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#0A1931"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#0A1931"))
    body = styles["Normal"]
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.grey)
    head_bg = colors.HexColor("#0A1931")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=f"{BRAND} Report", author=BRAND)
    s = [Paragraph(f"{BRAND} - Stock Risk Report", h1),
         Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                   f"Data: Yahoo Finance (1 year daily prices)", small),
         Spacer(1, 10), Paragraph("Summary", h2)]

    rows = [["Ticker", "Price (Rs.)", "1D %", "Volatility", "Max Drawdown", "3M Return", "Score", "Level"]]
    cmds = [("BACKGROUND", (0, 0), (-1, 0), head_bg), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")])]
    for i, r in enumerate(results, start=1):
        m = r["m"]
        r3 = "n/a" if np.isnan(m["ret_3m"]) else f"{m['ret_3m'] * 100:+.1f}%"
        rows.append([r["name"], f"{m['price']:.2f}", f"{m['change_1d']:+.2f}", f"{m['vol'] * 100:.1f}%",
                     f"{m['max_dd'] * 100:.1f}%", r3, str(r["score"]), r["level"]])
        cmds += [("BACKGROUND", (7, i), (7, i), r["color"]), ("TEXTCOLOR", (7, i), (7, i), colors.white)]
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    s.append(t)
    if failed:
        s += [Spacer(1, 8), Paragraph("Data not available for: " + ", ".join(failed), body)]

    s += [Spacer(1, 10), Paragraph("How the score works (0 = lowest risk, 100 = highest risk)", h2),
          Paragraph("40% annualized volatility (60% = maximum risk) + 40% maximum drawdown over 1 year "
                    "(50% fall = maximum risk) + 20% negative 3-month trend (30% fall = maximum risk). "
                    "GREEN below 35, YELLOW 35-64, RED 65 and above.", body)]

    for r in results:
        m = r["m"]
        vs, ds, ts = r["parts"]
        s += [PageBreak(), Paragraph(f"{r['name']} - Risk Score {r['score']}/100 ({r['level']})", h2),
              Image(chart_png(r["close"], r["name"]), width=17 * cm, height=6.3 * cm), Spacer(1, 8)]
        detail = [["Metric", "Value", "Risk part (0-100)"],
                  ["Annualized volatility", f"{m['vol'] * 100:.1f}%", str(vs)],
                  ["Max drawdown (1Y)", f"{m['max_dd'] * 100:.1f}%", str(ds)],
                  ["3-month return", "n/a" if np.isnan(m["ret_3m"]) else f"{m['ret_3m'] * 100:+.1f}%", str(ts)],
                  ["Last price date", m["last_date"], ""], ["Trading days used", str(m["days"]), ""]]
        dt = Table(detail, colWidths=[7 * cm, 5 * cm, 5 * cm])
        dt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), head_bg),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                                ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        s.append(dt)

    s += [Spacer(1, 16), Paragraph("Disclaimer: " + DISCLAIMER, small)]
    doc.build(s)
    return buf.getvalue()


# ---------- UI ----------
def results_frame(results):
    return pd.DataFrame([{
        "Ticker": r["name"], "Price (Rs.)": round(r["m"]["price"], 2),
        "Volatility %": round(r["m"]["vol"] * 100, 1),
        "Max Drawdown %": round(r["m"]["max_dd"] * 100, 1),
        "3M Return %": None if np.isnan(r["m"]["ret_3m"]) else round(r["m"]["ret_3m"] * 100, 1),
        "Risk Score": r["score"], "Level": r["level"]} for r in results])


def main():
    st.set_page_config(page_title=BRAND, page_icon="🛡️", layout="centered")
    st.title(f"🛡️ {BRAND}")
    st.caption("PSX stocks ka risk score (0-100) + PDF report. Asli price data, koi login nahi.")

    raw = st.text_input("Tickers (comma se alag karein)", value="OGDC, HUBC, LUCK, MCB",
                        help="PSX ke liye sirf naam likhein, jaise OGDC. Code khud .KA laga deta hai.")
    if st.button("Analyze", type="primary"):
        tickers = [normalize(x) for x in raw.split(",")]
        tickers = list(dict.fromkeys(t for t in tickers if t))     # duplicates hatao
        if not tickers:
            st.warning("Kam az kam ek ticker likhein.")
            return
        if len(tickers) > MAX_TICKERS:
            st.info(f"Ek baar mein sirf {MAX_TICKERS} tickers. Pehle {MAX_TICKERS} li gayi hain.")
            tickers = tickers[:MAX_TICKERS]
        bar = st.progress(0.0)
        with st.spinner("Data le raha hun..."):
            results, failed = analyze(tickers, bar)
        bar.empty()
        st.session_state["out"] = (results, failed)

    if "out" in st.session_state:
        results, failed = st.session_state["out"]
        if failed:
            st.warning("Data nahi mila: " + ", ".join(failed))
        if not results:
            st.error("Kisi ticker ka data nahi mila. Naam check karein ya baad mein try karein.")
            return
        df = results_frame(results)
        tint = {"GREEN": "#c8f0d3", "YELLOW": "#fff2b8", "RED": "#f7c4c4"}
        st.dataframe(df.style.map(lambda v: f"background-color: {tint.get(v, '')}; color: black"
                                  if v in tint else "", subset=["Level"]),
                     use_container_width=True, hide_index=True)
        for r in results:
            with st.expander(f"{r['name']} - {r['score']}/100 ({r['level']})"):
                st.line_chart(r["close"], height=200)
        c1, c2 = st.columns(2)
        c1.download_button("📄 PDF report download", build_pdf(results, failed),
                           file_name=f"RiskVault_Report_{datetime.now():%Y-%m-%d}.pdf",
                           mime="application/pdf")
        c2.download_button("📊 CSV download", df.to_csv(index=False),
                           file_name="riskvault_results.csv", mime="text/csv")
    st.divider()
    st.caption(DISCLAIMER)


if __name__ == "__main__":
    main()
  
