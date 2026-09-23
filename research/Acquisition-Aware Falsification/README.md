# Trapped by Stability — Quarto manuscript

The web version of *Trapped by Stability: A Falsification Framework for
Acquisition-Driven Radiomic Phenotypes*.

**The text on this page is the manuscript verbatim.** Headings, paragraphs,
figure and table captions, and table contents are exactly as written in the Word
document, extracted from it programmatically rather than retyped. Section and
table numbers are the author's own, so Quarto's automatic numbering and
cross-referencing are deliberately switched off — they would renumber them.

Two things are edited rather than verbatim, both at the author's request:
spelling and grammar slips are corrected, and the inline citations are converted
to `@key` form so the bibliography is live. Everything else is as written.

## Internal links

Quarto's automatic cross-referencing is off, because it renumbers — the
manuscript's own figure and table numbers are authoritative (note that it has no
Table 12, and that its last two tables are numbered 13 and 14).

Links are therefore hand-anchored to the author's numbers. Each caption carries
an anchor derived from its own text: `Table 5.` becomes `#t-5`,
`Supplementary Figure S2.` becomes `#f-s2`. Every "Table N" and "Figure N"
mention in the body is linked to the matching anchor. The ids deliberately avoid
the `tbl-` and `fig-` prefixes, which Quarto reserves — using those makes it
inject its own "Table 5" label above the author's caption.

Citations link to the reference list via `link-citations`, and preview on hover.
Two references the manuscript lists but never cites in text are kept in the list
by the `nocite` entry in the front matter.

Beyond that the project adds presentation only: typography, redrawn figures in
the site palette with light and dark variants, formatted tables, and one
interactive figure. `_theme.EDITORIAL_TITLES` is `False`, which suppresses in-figure
headlines so that every word a reader sees comes from the manuscript.

The figures are drawn from the analysis pipeline's own outputs, so the numbers
in them are not transcribed by hand.

## Layout

```
index.qmd         the manuscript
references.bib    27 references, live via citeproc
_theme.py         figure palette + typography, mirrors assets/theme-*.scss
_figures.py       every figure, as a function of (fig, palette)
_prep/            one-time export from the analysis repo (not needed to render)
_data/            slim CSVs the page reads (≈200 KB, committed)
figures/          rendered SVGs, light + dark (committed; the PNGs are unused
                  raster copies and can be deleted)
```

Files and folders beginning with `_` are ignored by Quarto's renderer.

## Rendering

Needs Python with `jupyter`, `ipykernel`, `pandas` and `matplotlib`:

```bash
pip install jupyter ipykernel pandas matplotlib
quarto render "research/Acquisition-Aware Falsification/index.qmd"
```

That builds HTML only, and needs nothing beyond the Python packages above.

**The PDF is deliberately not part of the default render.** Declaring a second
format in the front matter makes every whole-site `quarto render` build a PDF as
well, and that needs Chrome on the PATH (to rasterize the Mermaid diagram) plus a
network fetch for a Typst package the first time. If either is unavailable the
failure takes the entire site render down with it — not just this page.

Build it on demand instead:

```bash
quarto render "research/Acquisition-Aware Falsification/index.qmd" --to typst
```

If you want it back in the front matter permanently — and have confirmed that
command works on your machine — add this under `format:` alongside `html:`:

```yaml
  typst:
    papersize: a4
    margin: {x: 2.4cm, y: 2.6cm}
    fontsize: 10pt
    section-numbering: "1.1"
```

That also restores the "Other Formats → Typst" link in the page sidebar.

If `figures/` is missing, the setup chunk rebuilds it automatically.

## Regenerating the data layer

Only needed if the analysis pipeline is re-run. `_prep/export_data.py` reads the
full analysis repo and writes `_data/`:

```bash
RADIOMICS_REPO="<path to the analysis repo>" python3 _prep/export_data.py
```

It recomputes PCA variance by SVD, computes acquisition η² and its sensitivity
analysis, derives the Kaplan–Meier curves, and copies the pipeline's small result
tables. Deliberately, it needs only pandas and numpy — no sklearn, scipy or
lifelines — so rendering the site never requires the analysis environment.
