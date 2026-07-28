from flask import Flask, render_template, request
from magic_formula import run_magic_formula

app = Flask(__name__)

# Preset stock lists
STOCK_PRESETS = {
    "default": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "META",
        "NVDA",
        "BRK-B",
        "JNJ",
        "PG",
        "UNH",
        "HD",
        "BAC",
        "PFE",
        "XOM",
        "TSLA",
        "COST",
        "DIS",
        "CSCO",
        "CVX",
        "ORCL",
    ],
    "sp500_top": [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "BRK-B",
        "LLY",
        "AVGO",
        "JPM",
        "TSLA",
        "WMT",
        "UNH",
        "V",
        "XOM",
        "MA",
        "PG",
        "JNJ",
        "HD",
        "COST",
        "ABBV",
        "MRK",
        "ORCL",
        "CVX",
        "BAC",
    ],
    "tech_leaders": [
        "AAPL",
        "MSFT",
        "NVDA",
        "GOOGL",
        "AMZN",
        "META",
        "AVGO",
        "CSCO",
        "ADBE",
        "CRM",
        "AMD",
        "QCOM",
        "TXN",
        "INTC",
        "AMAT",
        "MU",
        "PANW",
    ],
    "dividend_giants": [
        "JNJ",
        "PG",
        "KO",
        "PEP",
        "XOM",
        "CVX",
        "MCD",
        "MMM",
        "IBM",
        "ABBV",
        "T",
        "VZ",
        "WMT",
        "CAT",
        "LOW",
        "TXN",
    ],
}


@app.route("/", methods=["GET", "POST"])
def index():
    tickers_input = ", ".join(STOCK_PRESETS["default"])
    min_cap = 500  # Default $500M
    exclude_fin_util = True
    active_preset = "default"

    if request.method == "POST":
        # Check if a preset button was pressed
        preset_action = request.form.get("preset")

        if preset_action and preset_action in STOCK_PRESETS:
            active_preset = preset_action
            tickers_list = STOCK_PRESETS[preset_action]
            tickers_input = ", ".join(tickers_list)
        else:
            raw_tickers = request.form.get("tickers", "")
            tickers_input = raw_tickers
            tickers_list = [
                t.strip().upper() for t in raw_tickers.split(",") if t.strip()
            ]

        try:
            min_cap = float(request.form.get("min_market_cap", 500))
        except ValueError:
            min_cap = 500

        exclude_fin_util = "exclude_fin_util" in request.form

        results_df = run_magic_formula(
            tickers_list,
            min_market_cap_m=min_cap,
            exclude_financials_utilities=exclude_fin_util,
        )
    else:
        results_df = run_magic_formula(
            STOCK_PRESETS["default"],
            min_market_cap_m=min_cap,
            exclude_financials_utilities=exclude_fin_util,
        )

    records = results_df.to_dict(orient="records") if not results_df.empty else []

    return render_template(
        "index.html",
        results=records,
        tickers_input=tickers_input,
        min_cap=min_cap,
        exclude_fin_util=exclude_fin_util,
        active_preset=active_preset,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
