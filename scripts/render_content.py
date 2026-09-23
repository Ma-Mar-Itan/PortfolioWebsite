"""Generate Quarto partials from structured portfolio data.

The generated files are committed so editor previews have sensible content even
before the project pre-render hook runs. Run this script after changing data in
``data/publications.json``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "publications.json"
OUT = ROOT / "_generated"
HOME_LIMIT = 3


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def authors_html(authors: list[dict[str, object]]) -> str:
    rendered = []
    for author in authors:
        name = esc(author["name"])
        rendered.append(f"<strong>{name}</strong>" if author.get("self") else name)
    if len(rendered) == 1:
        return rendered[0]
    if len(rendered) == 2:
        return " &amp; ".join(rendered)
    return ", ".join(rendered[:-1]) + ", &amp; " + rendered[-1]


def publication_list(publications: list[dict[str, object]]) -> str:
    rows = []
    for publication in publications:
        meta = authors_html(publication["authors"])
        if publication.get("venue"):
            meta += f" · <em>{esc(publication['venue'])}</em>"

        if publication.get("url"):
            status = (
                f'<a class="pub-link" href="{esc(publication["url"])}" '
                f'aria-label="Open publication: {esc(publication["title"])}">'
                'Paper <span aria-hidden="true">→</span></a>'
            )
        else:
            status = f'<span class="pub-pill">{esc(publication["status"])}</span>'

        rows.append(
            "\n".join(
                [
                    '  <li class="pub-row">',
                    f'    <div class="pub-year">{esc(publication["year"])}</div>',
                    '    <div class="pub-body">',
                    f'      <div class="pub-title">{esc(publication["title"])}</div>',
                    f'      <div class="pub-meta">{meta}</div>',
                    "    </div>",
                    f'    <div class="pub-status">{status}</div>',
                    "  </li>",
                ]
            )
        )
    return "```{=html}\n<ol class=\"pub-list\">\n" + "\n".join(rows) + "\n</ol>\n```\n"


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    return singular if count == 1 else (plural_form or singular + "s")


def main() -> None:
    publications = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)

    published = sum(p["status"].lower() == "published" for p in publications)
    under_review = sum(p["status"].lower() == "under review" for p in publications)
    project_count = sum(1 for path in (ROOT / "research").glob("*/index.qmd") if path.is_file())
    omitted = max(0, len(publications) - HOME_LIMIT)

    (OUT / "publications-home.qmd").write_text(
        publication_list(publications[:HOME_LIMIT]), encoding="utf-8"
    )
    (OUT / "publications-all.qmd").write_text(
        publication_list(publications), encoding="utf-8"
    )
    (OUT / "publications-count.qmd").write_text(
        f"{published} published · {under_review} under review\n", encoding="utf-8"
    )
    (OUT / "publications-home-summary.qmd").write_text(
        (
            f"{omitted} further co-authored {plural(omitted, 'paper')} are under review — "
            "[see the full list](research/index.qmd#publications).\n"
            if omitted
            else "[See the full publication list](research/index.qmd#publications).\n"
        ),
        encoding="utf-8",
    )
    (OUT / "research-stats.qmd").write_text(
        "\n".join(
            [
                "::: {.page-stats}",
                "::: {.stat}",
                f"[{project_count}]{{.stat-value}}",
                f"[{plural(project_count, 'Project')}]{{.stat-label}}",
                ":::",
                "::: {.stat}",
                f"[{len(publications)}]{{.stat-value}}",
                f"[{plural(len(publications), 'Publication')}]{{.stat-label}}",
                ":::",
                ":::",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
