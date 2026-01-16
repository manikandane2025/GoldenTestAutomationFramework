import json
import sys
from datetime import datetime

def load_summary(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_metric(summary: dict, name: str, key: str):
    metric = summary.get("metrics", {}).get(name, {})
    return metric.get(key)

def build_html(summary: dict) -> str:
    p95 = get_metric(summary, "http_req_duration", "p(95)")
    avg = get_metric(summary, "http_req_duration", "avg")
    maxv = get_metric(summary, "http_req_duration", "max")
    fail_rate = get_metric(summary, "http_req_failed", "rate")
    checks_rate = get_metric(summary, "checks", "rate")

    def fmt(val, digits=2):
        if val is None:
            return "n/a"
        return f"{val:.{digits}f}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>K6 Summary Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0b0f1a; color: #e6edf3; padding: 24px; }}
    .card {{ background: #121826; border: 1px solid #1f2937; border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
    h1 {{ font-size: 20px; margin: 0 0 12px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #1f2937; }}
    .muted {{ color: #9aa4b2; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>K6 Summary Report</h1>
    <div class="muted">Generated: {datetime.utcnow().isoformat()}Z</div>
  </div>
  <div class="card">
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>http_req_duration p95 (ms)</td><td>{fmt(p95)}</td></tr>
      <tr><td>http_req_duration avg (ms)</td><td>{fmt(avg)}</td></tr>
      <tr><td>http_req_duration max (ms)</td><td>{fmt(maxv)}</td></tr>
      <tr><td>http_req_failed rate</td><td>{fmt(fail_rate, 4)}</td></tr>
      <tr><td>checks rate</td><td>{fmt(checks_rate, 4)}</td></tr>
    </table>
  </div>
</body>
</html>
"""

def main():
    if len(sys.argv) < 3:
        print("Usage: python k6_report.py <summary_json> <output_html>")
        sys.exit(1)
    summary_path = sys.argv[1]
    output_path = sys.argv[2]
    summary = load_summary(summary_path)
    html = build_html(summary)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written: {output_path}")

if __name__ == "__main__":
    main()
