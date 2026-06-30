#!/usr/bin/env python3
"""Generate static HTML review for bakaknowledgeyan iteration results."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_md_files(outputs: Path) -> list[str]:
    if not outputs.is_dir():
        return []
    return sorted(str(p.relative_to(outputs)).replace("\\", "/") for p in outputs.rglob("*.md"))


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: generate_review_static.py <iteration-dir> <output.html>")
        sys.exit(1)
    iteration = Path(sys.argv[1]).resolve()
    out_html = Path(sys.argv[2]).resolve()
    benchmark = load_json(iteration / "benchmark.json") or {"runs": []}

    eval_dirs = sorted(
        p for p in iteration.iterdir() if p.is_dir() and (p / "eval_metadata.json").exists()
    )
    cases = []
    for ev in eval_dirs:
        meta = load_json(ev / "eval_metadata.json") or {}
        for config in ("with_skill", "without_skill"):
            outputs = ev / config / "outputs"
            grading = load_json(outputs / "grading.json") or {}
            cases.append(
                {
                    "id": f"{ev.name}-{config}",
                    "eval_name": meta.get("eval_name", ev.name),
                    "config": config,
                    "prompt": meta.get("prompt", ""),
                    "files": list_md_files(outputs),
                    "grading": grading,
                    "outputs_path": str(outputs),
                }
            )

    data_js = json.dumps(cases, indent=2)
    bench_js = json.dumps(benchmark, indent=2)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>bakaknowledgeyan — iteration review</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    nav button {{ margin-right: 0.5rem; }}
    .panel {{ border: 1px solid #ccc; padding: 1rem; border-radius: 6px; margin: 1rem 0; }}
    pre {{ background: #f6f8fa; padding: 0.75rem; overflow: auto; font-size: 12px; }}
    .pass {{ color: #060; }}
    .fail {{ color: #900; }}
    textarea {{ width: 100%; height: 80px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    td, th {{ border: 1px solid #ddd; padding: 0.4rem; text-align: left; }}
  </style>
</head>
<body>
  <h1>bakaknowledgeyan eval review</h1>
  <p>Iteration: {html.escape(iteration.name)}</p>
  <nav>
    <button onclick="showTab('outputs')">Outputs</button>
    <button onclick="showTab('benchmark')">Benchmark</button>
  </nav>
  <div id="outputs" class="panel">
    <button onclick="prevCase()">← Prev</button>
    <button onclick="nextCase()">Next →</button>
    <span id="case-label"></span>
    <h2>Prompt</h2>
    <pre id="prompt"></pre>
    <h2>Output files</h2>
    <ul id="files"></ul>
    <h2>Grades</h2>
    <ul id="grades"></ul>
    <h2>Feedback</h2>
    <textarea id="feedback" placeholder="Notes for this run…"></textarea>
    <button onclick="exportFeedback()">Export feedback.json</button>
  </div>
  <div id="benchmark" class="panel" style="display:none">
    <table id="bench-table"></table>
  </div>
  <script>
    const cases = {data_js};
    const benchmark = {bench_js};
    let idx = 0;
    const feedback = {{}};

    function showTab(name) {{
      document.getElementById('outputs').style.display = name === 'outputs' ? 'block' : 'none';
      document.getElementById('benchmark').style.display = name === 'benchmark' ? 'block' : 'none';
      if (name === 'benchmark') renderBench();
    }}

    function renderCase() {{
      const c = cases[idx];
      document.getElementById('case-label').textContent = `${{idx+1}}/${{cases.length}} — ${{c.eval_name}} (${{c.config}})`;
      document.getElementById('prompt').textContent = c.prompt;
      document.getElementById('files').innerHTML = c.files.map(f => `<li><code>${{f}}</code></li>`).join('') || '<li>(no .md files)</li>';
      const exp = (c.grading.expectations || []);
      document.getElementById('grades').innerHTML = exp.map(e =>
        `<li class="${{e.passed ? 'pass' : 'fail'}}">${{e.passed ? '✓' : '✗'}} ${{e.text}} <small>${{e.evidence || ''}}</small></li>`
      ).join('') || '<li>No grading.json yet</li>';
      document.getElementById('feedback').value = feedback[c.id] || '';
    }}

    function prevCase() {{ idx = (idx - 1 + cases.length) % cases.length; renderCase(); }}
    function nextCase() {{ idx = (idx + 1) % cases.length; renderCase(); }}
    document.getElementById('feedback').addEventListener('input', e => {{
      feedback[cases[idx].id] = e.target.value;
    }});

    function renderBench() {{
      const rows = benchmark.runs || [];
      let html = '<tr><th>Eval</th><th>Config</th><th>Pass rate</th><th>Passed</th><th>Tokens</th><th>Duration</th></tr>';
      for (const r of rows) {{
        html += `<tr><td>${{r.eval_name}}</td><td>${{r.config}}</td><td>${{(r.pass_rate*100).toFixed(0)}}%</td><td>${{r.passed}}/${{r.total}}</td><td>${{r.total_tokens ?? '-'}}</td><td>${{r.duration_ms ?? '-'}}</td></tr>`;
      }}
      document.getElementById('bench-table').innerHTML = html;
    }}

    function exportFeedback() {{
      const reviews = cases.map(c => ({{ run_id: c.id, feedback: feedback[c.id] || '', timestamp: new Date().toISOString() }}));
      const blob = new Blob([JSON.stringify({{ reviews, status: 'complete' }}, null, 2)], {{type: 'application/json'}});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'feedback.json';
      a.click();
    }}

    renderCase();
  </script>
</body>
</html>
"""
    out_html.write_text(page, encoding="utf-8")
    print(f"Wrote {out_html}")


if __name__ == "__main__":
    main()
