# Portfolio website

A [Quarto](https://quarto.org) website. Built and previewed in Positron.

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
categories: [tag, another-tag]
image: ../../../assets/img/thumb-1.svg
---
```

Assets for the post live in its own folder. The listing picks it up
automatically — no index to maintain.

## Adding a project or prototype

Same idea, one level shallower:
`research/my-project/index.qmd` or `prototypes/my-thing/index.qmd`, with
`image: ../../assets/img/thumb-1.svg`.

## Before publishing

- Set `site-url` in `_quarto.yml` to your real domain (RSS and social cards
  need it).
- Replace the `https://github.com/` and `https://www.linkedin.com/`
  placeholders in the navbar, footer, and about page.
- Swap `assets/img/portrait.svg` for a real photo and drop a real
  `assets/cv.pdf` in place.

## Publishing

    quarto publish gh-pages      # GitHub Pages
    quarto publish netlify       # Netlify

See <https://quarto.org/docs/publishing/>.
