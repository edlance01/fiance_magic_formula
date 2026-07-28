import yfinance as yf
import pandas as pd
import database


def fetch_financial_data(ticker_symbol):
    """Fetches financial balance sheet and income statement items via yfinance."""
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info

        # Financial Statements
        income = t.financials
        balance = t.balance_sheet

        if income.empty or balance.empty:
            return None

        # EBIT (Operating Income)
        ebit = (
            income.loc["Operating Income"].iloc[0]
            if "Operating Income" in income.index
            else None
        )
        if ebit is None and "EBIT" in income.index:
            ebit = income.loc["EBIT"].iloc[0]

        # Enterprise Value & Market Cap
        ev = info.get("enterpriseValue")
        market_cap = info.get("marketCap")

        # Working Capital & Fixed Assets
        total_current_assets = (
            balance.loc["Total Current Assets"].iloc[0]
            if "Total Current Assets" in balance.index
            else 0
        )
        total_current_liab = (
            balance.loc["Total Current Liabilities"].iloc[0]
            if "Total Current Liabilities" in balance.index
            else 0
        )
        net_working_capital = total_current_assets - total_current_liab

        net_fixed_assets = (
            balance.loc["Net PPE"].iloc[0] if "Net PPE" in balance.index else 0
        )

        if not ebit or not ev or ev <= 0:
            return None

        return {
            "ticker": ticker_symbol.upper(),
            "company_name": info.get("shortName", ticker_symbol),
            "sector": info.get("sector", "Unknown"),
            "market_cap": market_cap,
            "ebit": ebit,
            "enterprise_value": ev,
            "net_working_capital": net_working_capital,
            "net_fixed_assets": net_fixed_assets,
        }
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None


def run_magic_formula(
    ticker_list, min_market_cap_m=50, exclude_financials_utilities=True
):
    """Processes tickers, applies calculations, and generates combined rankings."""
    cached_df = database.get_cached_metrics(ticker_list)
    cached_tickers = set(cached_df["ticker"].tolist()) if not cached_df.empty else set()

    missing_tickers = [t for t in ticker_list if t.upper() not in cached_tickers]

    new_data = []
    for t in missing_tickers:
        data = fetch_financial_data(t)
        if data:
            new_data.append(data)

    if new_data:
        new_df = pd.DataFrame(new_data)
        database.save_metrics_to_cache(new_df)
        cached_df = pd.concat([cached_df, new_df], ignore_index=True)

    if cached_df.empty:
        return pd.DataFrame()

    df = cached_df.copy()

    # Filter Utilities & Financials if requested
    if exclude_financials_utilities:
        excluded = ["Financial Services", "Utilities", "Financials"]
        df = df[~df["sector"].isin(excluded)]

    # Filter Market Cap
    min_cap = min_market_cap_m * 1_000_000
    df = df[df["market_cap"] >= min_cap]

    # Calculations
    # 1. Earnings Yield = EBIT / EV
    df["earnings_yield"] = df["ebit"] / df["enterprise_value"]

    # 2. Return on Capital (ROC) = EBIT / (Net Working Capital + Net Fixed Assets)
    tangible_capital = df["net_working_capital"] + df["net_fixed_assets"]
    # Avoid zero division
    tangible_capital = tangible_capital.apply(lambda x: x if x > 0 else 1)
    df["roc"] = df["ebit"] / tangible_capital

    # Rankings
    df["ey_rank"] = df["earnings_yield"].rank(ascending=False, method="min")
    df["roc_rank"] = df["roc"].rank(ascending=False, method="min")
    df["combined_rank"] = df["ey_rank"] + df["roc_rank"]

    # Final sort
    df = df.sort_values(by="combined_rank", ascending=True).reset_index(drop=True)
    df["final_rank"] = df.index + 1

    return df
