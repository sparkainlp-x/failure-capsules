"""Build the static GitHub Pages demo for Failure Capsules.

Usage: python scripts/build_site.py _site

The page is generated at build time by the same standard-library code the CLI
uses: the checked-in example capsule is checked, its SYNTHETIC replay is
generated and drawn as an inline SVG, and a fixed set of deliberately broken
capsules is run through the validator so the real error messages are shown.
The output is one self-contained index.html: no JavaScript, no external
requests, no fonts or trackers.
"""

from __future__ import annotations

import copy
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from failure_capsules import (  # noqa: E402
    GENERATOR_NAME,
    SCHEMA_VERSION,
    generate_replay,
    validate_capsule,
)

EXAMPLE = ROOT / "examples" / "example_capsule.json"
VERSION = "0.1.0"


def _broken_cases(example: dict) -> list[tuple[str, str, dict]]:
    """Return (title, explanation, capsule) for each deliberately broken capsule."""
    cases = []

    raw = copy.deepcopy(example)
    raw["replay"]["samples"] = [100.1, 100.4, 99.8, 100.2]
    cases.append((
        "Original samples smuggled in",
        "A known raw-data key name (samples) anywhere in the capsule is rejected.",
        raw,
    ))

    unknown = copy.deepcopy(example)
    unknown["incident_id"] = "INC-2026-0417"
    cases.append((
        "An extra identifier field",
        "Unknown fields are rejected, so additions are visible and need a schema change.",
        unknown,
    ))

    numeric = copy.deepcopy(example)
    numeric["coarse_features"]["peak_level_bucket"] = "101.2, 102.9, 104.4"
    cases.append((
        "Numbers disguised as a category",
        "Feature values that look like a list of numbers are rejected (a heuristic, not a guarantee).",
        numeric,
    ))

    timestamp = copy.deepcopy(example)
    timestamp["timestamp_policy"] = {"policy": "rounded_hour_utc", "value": "2026-09-29T14:37:12Z"}
    cases.append((
        "A timestamp more precise than its policy",
        "A rounded-hour policy must carry a timestamp at the start of an hour.",
        timestamp,
    ))

    recipe = copy.deepcopy(example)
    recipe["replay"]["recipe"]["points"] = 1_000_000
    recipe["replay"]["recipe"]["noise_stddev"] = -1
    cases.append((
        "An unbounded replay recipe",
        "Recipe values are bounded so every replay stays small and finite.",
        recipe,
    ))
    return cases


def _svg_chart(values: list[float], drift_start: int) -> str:
    """Return an accessible inline SVG line chart of the replay values."""
    width, height, pad = 720, 260, 36
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    step = (width - 2 * pad) / max(1, len(values) - 1)

    def xy(index: int, value: float) -> tuple[float, float]:
        x = pad + index * step
        y = height - pad - (value - low) / span * (height - 2 * pad)
        return round(x, 2), round(y, 2)

    points = " ".join(f"{x},{y}" for x, y in (xy(i, v) for i, v in enumerate(values)))
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="3"><title>point {i}: {v}</title></circle>'
        for i, (x, y), v in ((i, xy(i, v), v) for i, v in enumerate(values))
    )
    drift_x = round(pad + drift_start * step, 2)
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-labelledby="chart-title chart-desc">'
        f'<title id="chart-title">SYNTHETIC replay, {len(values)} points</title>'
        f'<desc id="chart-desc">Flat synthetic baseline near {values[0]:.1f} with small noise, '
        f'then a linear drift starting at point {drift_start}, ending at {values[-1]:.1f}.</desc>'
        f'<line class="axis" x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}"/>'
        f'<line class="drift" x1="{drift_x}" y1="{pad / 2}" x2="{drift_x}" y2="{height - pad}"/>'
        f'<text class="label" x="{drift_x + 6}" y="{pad / 2 + 12}">drift_start = {drift_start}</text>'
        f'<text class="label" x="{pad}" y="{height - 10}">point 0</text>'
        f'<text class="label end" x="{width - pad}" y="{height - 10}">point {len(values) - 1}</text>'
        f'<polyline class="line" points="{points}"/>'
        f'<g class="dots">{dots}</g>'
        f"</svg>"
    )


CSS = """
:root{--navy:#0d1b2a;--panel:#13263a;--ink:#e8eef4;--muted:#a9b8c6;--gold:#c9a84c;--cyan:#4cc9e0;--bad:#f08a7e}
*{box-sizing:border-box}
body{margin:0;background:var(--navy);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--cyan)}a:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:1rem;top:1rem;background:var(--gold);color:var(--navy);padding:.4rem .7rem}
header,main,footer{max-width:960px;margin:0 auto;padding:1.25rem}
header{padding-top:2.5rem}
h1{font-size:2rem;margin:.2rem 0;color:var(--gold);letter-spacing:.01em}
h2{font-size:1.3rem;margin:2.2rem 0 .6rem;color:var(--gold)}
h3{font-size:1.02rem;margin:0 0 .3rem}
.tag{display:inline-block;font-size:.75rem;font-weight:700;letter-spacing:.08em;border:1px solid var(--cyan);color:var(--cyan);border-radius:4px;padding:.05rem .45rem}
.lede{color:var(--muted);max-width:46rem}
.card{background:var(--panel);border:1px solid #23405c;border-radius:10px;padding:1rem 1.1rem;margin:.8rem 0}
.ok{color:var(--cyan);font-weight:700}.bad{color:var(--bad);font-weight:700}
pre{background:#0a1522;border:1px solid #23405c;border-radius:8px;padding:.8rem;overflow:auto;font-size:.82rem;line-height:1.45;max-height:28rem}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.chart{width:100%;height:auto;background:#0a1522;border:1px solid #23405c;border-radius:8px}
.chart .axis{stroke:#35546f}.chart .drift{stroke:var(--gold);stroke-dasharray:5 5}
.chart .label{fill:var(--muted);font-size:12px}.chart .end{text-anchor:end}
.chart .line{fill:none;stroke:var(--cyan);stroke-width:2.5;stroke-linejoin:round;stroke-dasharray:2000;stroke-dashoffset:2000;animation:draw 2.4s ease-out forwards}
.chart .dots circle{fill:var(--gold)}
@keyframes draw{to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){.chart .line{animation:none;stroke-dashoffset:0}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.8rem}
ul.errors{margin:.4rem 0 0;padding-left:1.1rem;color:var(--bad);font-family:ui-monospace,monospace;font-size:.82rem}
details summary{cursor:pointer;color:var(--muted)}details summary:focus-visible{outline:2px solid var(--gold)}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{text-align:left;border-bottom:1px solid #23405c;padding:.35rem .4rem}
footer{color:var(--muted);font-size:.85rem;border-top:1px solid #23405c;margin-top:2.5rem}
"""


def render(example: dict) -> str:
    """Return the complete HTML page as a string."""
    errors = validate_capsule(example)
    if errors:
        raise SystemExit("example capsule is invalid: " + "; ".join(errors))
    recipe = example["replay"]["recipe"]
    seed = example["replay"]["seed"]
    values = generate_replay(seed, **recipe)
    esc = html.escape

    cases_html = []
    for title, why, capsule in _broken_cases(example):
        found = validate_capsule(capsule)
        if not found:
            raise SystemExit(f"broken case {title!r} unexpectedly passed validation")
        items = "".join(f"<li>{esc(e)}</li>" for e in found)
        cases_html.append(
            f'<article class="card"><h3>{esc(title)}</h3><p>{esc(why)}</p>'
            f'<p class="bad">Rejected, exit code 1</p><ul class="errors">{items}</ul></article>'
        )

    rows = "".join(
        f"<tr><td>{i}</td><td><code>{v}</code></td></tr>" for i, v in enumerate(values)
    )
    capsule_json = esc(json.dumps(example, indent=2, ensure_ascii=False))
    recipe_text = ", ".join(f"{k}={v}" for k, v in recipe.items())

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:">
<meta name="referrer" content="no-referrer">
<title>Failure Capsules: a SYNTHETIC replay demo</title>
<meta name="description" content="Offline incident capsules with a deterministic synthetic replay. Research prototype by Jean-François Brisson, Spark AI NLP.">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header>
<span class="tag">SYNTHETIC</span> <span class="tag">RESEARCH PROTOTYPE</span>
<h1>Failure Capsules</h1>
<p class="lede">Share an incident as a small, schema-checked JSON capsule plus a seeded recipe that regenerates an
artificial replay, instead of shipping the original measurements. This page was generated at build time by
the same standard-library Python code as the command-line tool (version {VERSION}, schema {SCHEMA_VERSION}).</p>
</header>
<main id="main">
<h2>1. The example capsule</h2>
<p><span class="ok">Valid, exit code 0.</span> Every value in it is synthetic. Note what is absent: no incident
identifier, no device serial, no samples.</p>
<details><summary>Show examples/example_capsule.json</summary><pre><code>{capsule_json}</code></pre></details>

<h2>2. Its replay, regenerated from the recipe</h2>
<p>Generator <code>{esc(GENERATOR_NAME)}</code>, seed <code>{seed}</code>, {esc(recipe_text)}. The same recipe and
seed produce the same values on CPython 3.x. These numbers are invented by the generator; they are not a
recording of any device.</p>
{_svg_chart(values, recipe["drift_start"])}
<details><summary>Show all {len(values)} SYNTHETIC values</summary>
<table><caption class="lede">SYNTHETIC replay values</caption><thead><tr><th scope="col">Point</th><th scope="col">Value</th></tr></thead><tbody>{rows}</tbody></table>
</details>

<h2>3. What the validator refuses</h2>
<p>Each card below is the example capsule with one deliberate mistake. The messages are the validator's own
output, captured when this page was built.</p>
<div class="grid">{"".join(cases_html)}</div>

<h2>Limits</h2>
<div class="card"><ul>
<li>It is a format guard, not a privacy scanner, anonymizer or de-identification tool. Passing validation
does not make a capsule safe to publish; free text and categories can still identify people or places.</li>
<li>All values on this page are SYNTHETIC. Use on real incident workflows is UNRUN.</li>
<li>The checklist booleans are self-reported; the tool does not verify them.</li>
<li>Replay determinism is stated for CPython 3.x only.</li>
</ul></div>
</main>
<footer>
<p>Failure Capsules {VERSION}. Copyright (c) 2026 Jean-François Brisson, Spark AI NLP. MIT License.
Source: <a href="https://github.com/sparkainlp-x/failure-capsules">github.com/sparkainlp-x/failure-capsules</a>.
This page makes no network requests and uses no JavaScript.</p>
</footer>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    out_dir = Path(args[0]) if args else ROOT / "_site"
    out_dir.mkdir(parents=True, exist_ok=True)
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    (out_dir / "index.html").write_text(render(example), encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
