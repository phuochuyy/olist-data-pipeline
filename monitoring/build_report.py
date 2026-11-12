#!/usr/bin/env python3
"""Build a static HTML report of the latest pipeline run.

Reads the warehouse (row counts per layer, business KPIs), the latest Great
Expectations summary and dbt's run_results.json, and writes one self-contained
HTML file (no JavaScript). The DAG task `build_html_report` writes docs/index.html,
which GitHub Pages serves.

    python monitoring/build_report.py --out docs/index.html --dsn "host=localhost dbname=olist_dw user=postgres password=postgres"
"""

import argparse
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]   # /opt/airflow in the container, the repo root locally
DEFAULT_DSN = "host=postgres port=5432 dbname=olist_dw user=postgres password=postgres"
LAYER_ORDER = {"bronze": 1, "silver": 2, "gold": 3, "analytics": 4}


def query(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def load_warehouse(dsn):
    with psycopg2.connect(dsn) as con, con.cursor() as cur:
        run_id, run_time = query(cur, """
            SELECT run_id, max(created_at) FROM monitoring.pipeline_metrics
            GROUP BY run_id ORDER BY max(created_at) DESC LIMIT 1""")[0]
        cur.execute("""SELECT layer, table_name, row_count FROM monitoring.pipeline_metrics
                       WHERE run_id = %s""", (run_id,))
        layers = sorted(cur.fetchall(), key=lambda r: (LAYER_ORDER.get(r[0], 9), r[1]))
        revenue, orders = query(cur, "SELECT sum(total_revenue), sum(total_orders) FROM marts.daily_sales_summary")[0]
        customers, repeat = query(cur, """SELECT count(*), count(*) FILTER (WHERE total_orders > 1)
                                          FROM marts.mart_customer_analytics""")[0]
        states = query(cur, """SELECT customer_state, total_revenue, total_orders
                               FROM analytics.revenue_by_state ORDER BY total_revenue DESC LIMIT 10""")
        months = query(cur, """SELECT to_char(month, 'YYYY-MM'), total_revenue, total_orders
                               FROM analytics.monthly_trends ORDER BY month""")
    return {
        "run_id": run_id, "run_time": run_time, "layers": layers,
        "kpis": {"revenue": float(revenue), "orders": int(orders), "aov": float(revenue) / int(orders),
                 "customers": customers, "repeat": repeat},
        "states": states, "months": months,
    }


def load_great_expectations(ge_dir):
    files = sorted(Path(ge_dir).glob("validation_*.json"))
    if not files:
        return None
    summary = json.loads(files[-1].read_text())
    rows = []
    for table, result in summary["tables"].items():
        checks = result["checks"]
        rows.append((f"raw.{table}", sum(c["success"] for c in checks), len(checks)))
    return {"run_at": summary["run_at"], "rows": rows}


def load_dbt(run_results):
    path = Path(run_results)
    if not path.exists():
        return None
    results = json.loads(path.read_text())["results"]
    tests = [r for r in results if r["unique_id"].startswith("test.")]
    models = [r for r in results if r["unique_id"].startswith("model.")]
    return {
        "models_ok": sum(r["status"] == "success" for r in models), "models": len(models),
        "tests_ok": sum(r["status"] == "pass" for r in tests), "tests": len(tests),
        "failed": [r["unique_id"].split(".")[-1] for r in tests if r["status"] != "pass"],
    }


def esc(value):
    return html.escape(str(value))


def money(value):
    return f"R$ {value:,.0f}"


def bars(rows, value_index, label_format=money):
    """Horizontal bars in plain HTML/CSS: (label, value, ...) rows."""
    top = max(float(r[value_index]) for r in rows) or 1
    out = []
    for r in rows:
        value = float(r[value_index])
        out.append(f'<div class="bar"><span class="bar-label">{esc(r[0])}</span>'
                   f'<span class="bar-track"><span class="bar-fill" style="width:{value / top * 100:.1f}%"></span></span>'
                   f'<span class="bar-value">{esc(label_format(value))}</span></div>')
    return "\n".join(out)


CSS = """
:root{--bg:#fff;--fg:#1f2328;--muted:#59636e;--line:#d0d7de;--soft:#f6f8fa;--accent:#0969da;--ok:#1a7f37;--bad:#cf222e}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--soft:#161b22;--accent:#4493f8;--ok:#3fb950;--bad:#f85149}}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:980px;margin:2rem auto;padding:0 16px;color:var(--fg);background:var(--bg);line-height:1.5}
h1{margin-bottom:.2rem}h2{margin-top:2.2rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
.muted{color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:1rem}
.kpi{border:1px solid var(--line);border-radius:8px;padding:12px;background:var(--soft)}
.kpi b{display:block;font-size:1.5rem}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{border-bottom:1px solid var(--line);padding:.4rem .5rem;text-align:left}th{color:var(--muted);font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}
.bar{display:grid;grid-template-columns:80px 1fr 130px;gap:8px;align-items:center;margin:3px 0;font-size:.9rem}
.bar-track{background:var(--soft);border-radius:4px;height:14px;overflow:hidden}
.bar-fill{display:block;height:100%;background:var(--accent)}
.bar-value{text-align:right;font-variant-numeric:tabular-nums}
footer{margin-top:3rem;font-size:.85rem}
"""


def render(wh, ge, dbt):
    k = wh["kpis"]
    status = lambda ok, total: f'<span class="{"ok" if ok == total else "bad"}">{ok}/{total} passed</span>'  # noqa: E731
    layer_rows = "\n".join(f'<tr><td>{esc(layer)}</td><td>{esc(table)}</td><td class="num">{count:,}</td></tr>'
                           for layer, table, count in wh["layers"])
    ge_rows = "\n".join(f"<tr><td>{esc(t)}</td><td>{status(ok, n)}</td></tr>" for t, ok, n in ge["rows"]) if ge else ""
    quality = [
        f'<tr><td>dbt models</td><td>{status(dbt["models_ok"], dbt["models"])}</td></tr>',
        f'<tr><td>dbt tests (not_null, unique, relationships, ranges)</td><td>{status(dbt["tests_ok"], dbt["tests"])}</td></tr>',
    ] if dbt else []
    if ge:
        ok = sum(r[1] for r in ge["rows"])
        total = sum(r[2] for r in ge["rows"])
        quality.append(f"<tr><td>Great Expectations on bronze tables</td><td>{status(ok, total)}</td></tr>")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Olist Pipeline Report</title><style>{CSS}</style></head><body>
<h1>Olist Pipeline Report</h1>
<p class="muted">Latest Airflow run <code>{esc(wh["run_id"])}</code>, finished {esc(f"{wh['run_time']:%Y-%m-%d %H:%M UTC}")}.
Data: Olist Brazilian e-commerce, delivered orders 2016-2018.</p>

<div class="kpis">
<div class="kpi"><span class="muted">Revenue (item price)</span><b>{money(k["revenue"])}</b></div>
<div class="kpi"><span class="muted">Delivered orders</span><b>{k["orders"]:,}</b></div>
<div class="kpi"><span class="muted">Average order value</span><b>R$ {k["aov"]:,.2f}</b></div>
<div class="kpi"><span class="muted">Customers</span><b>{k["customers"]:,}</b><span class="muted">{k["repeat"]:,} bought more than once</span></div>
</div>

<h2>Data quality</h2>
<table><tr><th>Check</th><th>Result</th></tr>
{"".join(quality)}
</table>
{f'<h3>Great Expectations per table</h3><table><tr><th>Table</th><th>Expectations</th></tr>{ge_rows}</table>' if ge else ""}

<h2>Rows per table</h2>
<table><tr><th>Layer</th><th>Table</th><th>Rows</th></tr>
{layer_rows}
</table>

<h2>Revenue by customer state (top 10)</h2>
{bars(wh["states"], 1)}

<h2>Revenue per month</h2>
{bars(wh["months"], 1)}

<footer class="muted">Generated {generated} by the <code>build_html_report</code> task of
<a href="https://github.com/phuochuyy/olist-data-pipeline">olist-data-pipeline</a>.</footer>
</body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "docs" / "index.html"))
    parser.add_argument("--dsn", default=os.environ.get("OLIST_DW_DSN", DEFAULT_DSN))
    parser.add_argument("--ge-dir", default=str(ROOT / "great_expectations" / "uncommitted"))
    parser.add_argument("--dbt-results", default=str(ROOT / "dbt_project" / "target" / "run_results.json"))
    args = parser.parse_args()

    page = render(load_warehouse(args.dsn), load_great_expectations(args.ge_dir), load_dbt(args.dbt_results))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"report written to {out}")


if __name__ == "__main__":
    main()
