import os
import shutil
from pathlib import Path

import pandas as pd
import xlwings as xw
from xlwings.reports import formatter
import matplotlib.pyplot as plt

from xbrl import Report


@formatter
def table(rng: xw.Range, df: pd.DataFrame):
    """Striped rows"""
    for ix, row in enumerate(rng.rows[1:]):
        if ix % 2 == 0:
            row.color = "#F0F0F0"  # Even rows


# We'll place this file in the same directory as the Excel template
this_dir = Path(__file__).resolve().parent

for subdir in ["pdf", "xlsx"]:
    os.makedirs(this_dir / "reports" / subdir, exist_ok=True)


def create_report(path):
    report = Report(path)

    # High-level balance sheet
    asofdate = report.get_latest_fact("Assets")["period_start"]
    current_assets = report.get_latest_fact("CurrentAssets")["value"]
    noncurrent_assets = report.get_latest_fact("NoncurrentAssets")["value"]
    liabilities = report.get_latest_fact("Liabilities")["value"]
    equity = report.get_latest_fact("Equity")["value"]
    balance_sheet = pd.DataFrame(
        {
            "Financing": [None, None, equity, liabilities],
            "Assets": [current_assets, noncurrent_assets, None, None],
        },
        index=["Current Assets", "Non-current Assets", "Equity", "Liabilties"],
    )
    balance_sheet = balance_sheet / 1_000_000

    # Equity components
    equity_components = pd.DataFrame(
        report.get_all_facts("ComponentsOfEquityAxis", subcomponent=True)
    )
    equity_components = equity_components.loc[equity_components["value"] != 0, :]
    equity_components = equity_components.loc[
        equity_components["period_start"] == asofdate, :
    ]
    equity_components = equity_components.sort_values("value", ascending=False)
    equity_components["value"] = equity_components["value"] / 1_000_000
    equity_components = equity_components[["name", "value"]]
    equity_components = equity_components.rename(
        columns={"name": "Equity type", "value": f"{report.currency} (m)"}
    )

    # Plot
    plt.style.use("fivethirtyeight")
    ax = (
        equity_components.sort_values(by=f"{report.currency} (m)")
        .set_index("Equity type")
        .plot.barh(figsize=(9, 6), color=["#00A83F"])
    )
    ax.set_ylabel("")
    ax.legend().set_visible(False)
    ax.set_xlabel(f"{report.currency}(m)")
    fig = ax.get_figure()

    data = dict(
        title=report.entity_name,
        currency=report.currency,
        description=report.entity_description,
        asofdate=asofdate,
        balance_sheet=balance_sheet.reset_index(),
        equity_components=equity_components,
        fig=fig,
    )

    book = xw.apps.active.render_template(
        this_dir / "template.xlsx",
        this_dir / "reports" / "xlsx" / "temp.xlsx",  # macOS requires permission
        **data,
    )

    filename = f"{report.entity_name.replace('/', '')}_{path.stem}"

    shutil.move(
        this_dir / "reports" / "xlsx" / "temp.xlsx",
        this_dir / "reports" / "xlsx" / f"{filename}.xlsx",
    )
    pdf_path = this_dir / "reports" / "pdf" / f"{filename}.pdf"
    book.to_pdf(path=pdf_path, layout=this_dir / "layout.pdf", show=True)
    book.close()
    return report


def main():
    book = xw.Book.caller()
    config = book.sheets["# options"]["A1"].expand().options(dict).value
    for ix, path in enumerate(Path(this_dir / "data").glob("*.json")):
        report = create_report(path)
        if config["number of reports"] == 1:
            break


if __name__ == "__main__":
    xw.Book.set_mock_caller(xw.Book("template.xlsx"))
    main()
