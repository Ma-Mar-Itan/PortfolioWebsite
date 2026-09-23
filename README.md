# Portfolio website

A [Quarto](https://quarto.org) website. Built and previewed in Positron.

## Setup

Install the local figure tooling and its Python dependencies once:

    python -m pip install -e .

The site is verified with Quarto 1.10.18 and Python 3.10 or newer.

## Preview

    quarto preview

Or in Positron: open the folder, then **Render** / the preview button on any
`.qmd`. The preview refreshes on save, including changes to `_quarto.yml`.

## Structure

    _quarto.yml                 site config: navbar, theme, footer, metadata
    index.qmd                   home page (hero + featured listings)
    about.qmd                   About me
    404.qmd                     custom not-found page
    styles.css                  one-off CSS tweaks
    home.css                    homepage composition
    blog.css                    blog listing composition
    research.css                research index composition
    prototypes.css              prototype-card composition
    data/publications.json      publication records (source of truth)
    scripts/                    content generation and site validation
    portfolio_figures/          shared Matplotlib theme helpers
    assets/
      theme-light.scss          colors, fonts, components (light)
      theme-dark.scss           dark-mode palette overrides
      img/                      logo, favicon, portrait, thumbnails
    blog/
      index.qmd                 blog listing + RSS feed
      posts/
        _metadata.yml           defaults applied to every post
        YYYY-MM-DD-slug/
          index.qmd             one post
    research/
      index.qmd                 project grid + publications list
      <project>/index.qmd       one project
    prototypes/
      index.qmd                 prototype grid
      <prototype>/index.qmd     one prototype

## Adding a blog post

Create `blog/posts/2026-09-01-my-slug/index.qmd`:

```yaml
---
title: "Post title"
description: "One sentence — this is the listing blurb."
date: 2026-09-01
draft: false
categories: [tag, another-tag]
image: ../../../assets/img/thumb-1.svg
---
```

Assets for the post live in its own folder. The listing picks it up
automatically — no index to maintain.

To keep a finished Markdown page available by direct URL without showing it on
the homepage, Blog, Research, search, feed, or sitemap, set:

```yaml
draft: true
```

The site uses `draft-mode: unlinked`, so the page still renders for private
previewing. Change it to `draft: false` (or remove the field) when it is ready
to appear publicly.

## Adding a project or prototype

Same idea, one level shallower:
`research/my-project/index.qmd` or `prototypes/my-thing/index.qmd`, with
`image: ../../assets/img/thumb-1.svg`.

## Updating publications

Edit `data/publications.json`. Quarto regenerates the homepage and research
partials before every render. To regenerate them without rendering:

    python scripts/render_content.py

## Validate

    quarto render
    python scripts/check_site.py _site

## Publishing

    quarto publish gh-pages      # GitHub Pages
    quarto publish netlify       # Netlify

See <https://quarto.org/docs/publishing/>.
