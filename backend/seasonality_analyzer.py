#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seasonality_analyzer.py

A small utility to:
1) Fetch up to 10 years of OHLC data via yfinance
2) Compute average monthly returns (seasonality) per ticker
3) Export a JSONL library (seasonal_patterns.jsonl)
4) Query Gemini 2.0 Flash for a concise seasonality assessment using the JSONL data

Usage examples:
  # Build JSONL for multiple tickers
  python seasonality_analyzer.py build-jsonl --tickers KINV-B.ST VOLV-B.ST HM-B.ST

  # Analyze a ticker for the current month (auto-detected)
  GEMINI_API_KEY=your_key python seasonality_analyzer.py analyze --ticker KINV-B.ST

  # Analyze a specific month number (1-12)
  GEMINI_API_KEY=your_key python seasonality_analyzer.py analyze --ticker VOLV-B.ST --month 12

Requirements (install):
  pip install yfinance pandas google-generativeai
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

# Gemini is optional until you run "analyze"
try:
    import google.generativeai as genai
except Exception:
    genai = None


# -----------------------------
# Core seasonality calculations
# -----------------------------

def get_monthly_returns(ticker: str, years: int = 10) -> Dict[int, float]:
    """
    Download daily data for 'years' years and compute average monthly returns.

    Returns:
        dict: {month(1..12): avg_return_decimal}, e.g. {1: 0.012, 2: -0.004, ...}
    """
    if years < 1:
        years = 1

    # yfinance period accepts '10y' etc.
    period_str = f"{years}y"
    df = yf.download(ticker, period=period_str, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    # Compute daily returns
    df["Return"] = df["Close"].pct_change()

    # Aggregate by (Year, Month) and sum daily returns
    df["Year"] = df.index.year
    df["Month"] = df.index.month
    monthly = df.groupby(["Year", "Month"])["Return"].sum().reset_index()

    # Average monthly return across years
    avg_returns = monthly.groupby("Month")["Return"].mean().round(6)

    # Turn into dict month->decimal
    return {int(m): float(r) for m, r in avg_returns.to_dict().items()}


def classify_bias(avg_return_dec: float, pos=0.01, neg=-0.01) -> Tuple[str, float]:
    """
    Classify a monthly average return into a bias label and a basic score (0-10).
    pos / neg are thresholds in decimal (e.g., +1% / -1%).
    """
    if avg_return_dec >= pos:
        bias = "bullish"
    elif avg_return_dec <= neg:
        bias = "bearish"
    else:
        bias = "neutral"
    score = round(min(abs(avg_return_dec) * 100.0, 10.0), 1)  # cap to 10 for display
    return bias, score


def build_jsonl(tickers: List[str], years: int = 10, out_path: str = "seasonal_patterns.jsonl") -> int:
    """
    Build a JSONL dataset of monthly seasonality for the given tickers.
    Each line is a JSON object:
      {"ticker": "VOLV-B.ST", "month": 12, "bias": "bullish", "avg_return_pct": 2.31, "score": 2.3}

    Returns:
        int: number of rows written
    """
    rows = []
    for t in tickers:
        try:
            monthly = get_monthly_returns(t, years=years)
        except Exception as e:
            print(f"[warn] {t}: {e}")
            continue

        for m in range(1, 13):
            r = monthly.get(m, 0.0)
            bias, score = classify_bias(r)
            rows.append({
                "ticker": t,
                "month": m,
                "bias": bias,
                "avg_return_pct": round(r * 100.0, 2),
                "score": score
            })

    if not rows:
        raise RuntimeError("No data rows generated. Check tickers or network.")

    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[OK] Wrote {len(rows)} rows to {out_path}")
    return len(rows)


# -----------------------------
# Gemini-based interpretation
# -----------------------------

GEMINI_MODEL_NAME = "gemini-2.0-flash"  # change if needed


def _init_gemini():
    if genai is None:
        raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL_NAME)


def _load_jsonl_subset(path: str, ticker: str, month: int, max_chars: int = 6000) -> str:
    """
    Load only relevant lines (same ticker + same month) and a few related samples
    to keep prompt size small. Fallback: include that ticker across all months.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run build-jsonl first.")

    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("ticker") == ticker and obj.get("month") == month:
                    lines.append(obj)
            except Exception:
                continue

    # If we didn't get anything for that month, include a full-year snapshot for the ticker
    if not lines:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("ticker") == ticker:
                        lines.append(obj)
                except Exception:
                    continue

    # Hard cap the prompt size
    buf = json.dumps(lines, ensure_ascii=False)
    if len(buf) > max_chars:
        buf = buf[:max_chars]

    return buf


def gemini_seasonality_analysis(ticker: str, month: int, jsonl_path: str = "seasonal_patterns.jsonl") -> dict:
    """
    Ask Gemini for a short seasonality assessment with a 0-10 score.
    Returns a dict with fields: {month, bias, ai_score, rationale}
    """
    model = _init_gemini()
    month = int(month)
    subset = _load_jsonl_subset(jsonl_path, ticker, month)

    month_name = datetime(2000, month, 1).strftime("%B")
    sys_prompt = (
        "Du är en aktieanalys-assistent. Du får ett utdrag av historiska säsongsdata "
        "i JSON-listformat (från seasonal_patterns.jsonl). Ditt jobb är att ge en RAK "
        "och KORT bedömning för en specifik ticker och månad, som JSON:\n\n"
        '{ "month": <1-12>, "bias": "bullish|neutral|bearish", "ai_score": 0-10, "rationale": "kort förklaring" }\n\n'
        "Viktigt: ai_score ska spegla hur stark säsongseffekten är enligt datan (0-10). "
        "Var saklig och undvik överdrifter."
    )

    user_prompt = (
        f"Ticker: {ticker}\n"
        f"Månad: {month} ({month_name})\n\n"
        f"Relevant säsongsdata (JSON-utdrag):\n{subset}\n\n"
        "Ge ett enda JSON-objekt som svar."
    )

    resp = model.generate_content([sys_prompt, user_prompt])
    text = getattr(resp, "text", "").strip()
    # Attempt to parse JSON in the response
    try:
        if text.startswith("```"):
            # strip code fences if present
            text = text.strip("`").strip()
            # try to find JSON inside
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end+1]
        data = json.loads(text)
    except Exception:
        data = {"error": "Failed to parse Gemini response", "raw": text}

    return data


# -----------------------------
# CLI
# -----------------------------

def _cmd_build_jsonl(args):
    tickers = args.tickers
    years = args.years
    out = args.out
    build_jsonl(tickers, years=years, out_path=out)


def _cmd_analyze(args):
    ticker = args.ticker
    month = args.month or datetime.now().month
    result = gemini_seasonality_analysis(ticker, month, jsonl_path=args.jsonl)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Seasonality analyzer + Gemini scorer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("build-jsonl", help="Build seasonal_patterns.jsonl for given tickers")
    p1.add_argument("--tickers", nargs="+", required=True, help="List of tickers (e.g., VOLV-B.ST KINV-B.ST)")
    p1.add_argument("--years", type=int, default=10, help="Years of history (default 10)")
    p1.add_argument("--out", default="seasonal_patterns.jsonl", help="Output JSONL path")
    p1.set_defaults(func=_cmd_build_jsonl)

    p2 = sub.add_parser("analyze", help="Ask Gemini for seasonality assessment for a ticker/month")
    p2.add_argument("--ticker", required=True, help="Ticker (e.g., VOLV-B.ST)")
    p2.add_argument("--month", type=int, help="Month number 1..12 (default: current month)")
    p2.add_argument("--jsonl", default="seasonal_patterns.jsonl", help="Path to seasonal_patterns.jsonl")
    p2.set_defaults(func=_cmd_analyze)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
