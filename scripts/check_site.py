"""Fail when rendered HTML points to a missing local file."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


IGNORED_SCHEMES = {"data", "http", "https", "javascript", "mailto", "tel"}


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        wanted = "href" if tag in {"a", "link"} else "src" if tag in {"img", "script", "source"} else None
        if not wanted:
            return
        for name, value in attrs:
            if name == wanted and value:
                self.values.append(value)


def candidate_path(site: Path, page: Path, reference: str, base_path: str) -> Path | None:
    parsed = urlsplit(reference)
    if parsed.scheme.lower() in IGNORED_SCHEMES or reference.startswith("//"):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path.startswith(base_path):
        path = path[len(base_path):]
    if path.startswith("/"):
        return site / path.lstrip("/")
    return page.parent / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", default="_site")
    parser.add_argument("--base-path", default="/PortfolioWebsite/")
    args = parser.parse_args()
    site = Path(args.site).resolve()
    missing: list[tuple[Path, str]] = []

    for page in site.rglob("*.html"):
        references = References()
        references.feed(page.read_text(encoding="utf-8", errors="replace"))
        for reference in references.values:
            candidate = candidate_path(site, page, reference, args.base_path)
            if candidate is None:
                continue
            if candidate.is_dir():
                candidate /= "index.html"
            if not candidate.exists():
                missing.append((page.relative_to(site), reference))

    if missing:
        for page, reference in sorted(set(missing)):
            print(f"{page}: missing {reference}")
        return 1
    print(f"Local link check passed for {sum(1 for _ in site.rglob('*.html'))} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
