from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path

from public_site.constants import HEADER_LOGO_PUBLIC_PATH, HOME_HERO_PUBLIC_PATH
from public_site.manifest import public_sidebar_section
from public_site.models import PageEntry, SessionNavLink


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_jekyll_config(output_dir: Path, manifest: dict) -> None:
    site = manifest["site"]
    config_text = textwrap.dedent(
        f"""\
        title: {yaml_string(site['title'])}
        description: {yaml_string(site['description'])}
        lang: "it"
        url: {yaml_string(site.get('url', ''))}
        baseurl: {yaml_string(site.get('baseurl', ''))}
        tagline: {yaml_string(site.get('tagline', ''))}
        defaults:
          - scope:
              path: ""
            values:
              layout: default
        markdown: kramdown
        kramdown:
          input: GFM
          hard_wrap: false
        """
    )
    (output_dir / "_config.yml").write_text(config_text, encoding="utf-8")


def write_layout(output_dir: Path) -> None:
    layout_dir = output_dir / "_layouts"
    layout_dir.mkdir(parents=True, exist_ok=True)
    layout_text = textwrap.dedent(
        """\
        <!doctype html>
        <html lang="it">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="color-scheme" content="dark">
            <meta name="theme-color" content="#12100d">
            <meta name="apple-mobile-web-app-status-bar-style" content="black">
            <title>{% if page.title %}{{ page.title }} | {{ site.title }}{% else %}{{ site.title }}{% endif %}</title>
            <meta name="description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            {% if page.og_image %}
            <meta property="og:type" content="website">
            <meta property="og:site_name" content="{{ site.title | escape }}">
            <meta property="og:title" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.title | escape }}{% endif %}">
            <meta property="og:description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            <meta property="og:url" content="{{ page.url | absolute_url }}">
            <meta property="og:image" content="{{ page.og_image | absolute_url }}">
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.title | escape }}{% endif %}">
            <meta name="twitter:description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            <meta name="twitter:image" content="{{ page.og_image | absolute_url }}">
            {% endif %}
            <link rel="stylesheet" href="{{ '/assets/site.css' | relative_url }}">
            <link rel="icon" type="image/png" href="/assets/favicon-96x96.png" sizes="96x96" />
            <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
            <link rel="shortcut icon" href="/assets/favicon.ico" />
            <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png" />
            <link rel="manifest" href="/assets/site.webmanifest" />
          </head>
          <body{% if page.home_full_bleed and page.hero_image %} class="home-full-bleed" style="--home-hero-image: url('{{ page.hero_image | relative_url }}')"{% endif %}>
            <header class="site-header">
              <div class="site-header-inner">
                <div class="site-header-brand">
                  <a class="site-title site-title-logo" href="{{ '/' | relative_url }}">
                    <img src="@HEADER_LOGO_LIQUID@" alt="{{ site.title | escape }}" decoding="async">
                  </a>
                  {% if site.tagline and site.tagline != "" %}
                  <p class="site-tagline">{{ site.tagline }}</p>
                  {% endif %}
                </div>
              </div>
            </header>
            <div class="site-shell">
              <aside class="site-sidebar">
                <nav class="site-sidebar-nav" aria-label="Sezioni">
                  <a href="{{ '/personaggi/' | relative_url }}">Personaggi</a>
                  <a href="{{ '/resoconti/' | relative_url }}">Resoconti</a>
                  <a href="{{ '/png/' | relative_url }}">PNG</a>
                  <a href="{{ '/luoghi/' | relative_url }}">Luoghi</a>
                  <a href="{{ '/prompt/' | relative_url }}">Generatore</a>
                </nav>
              </aside>
              <div class="site-content">
                <main class="site-main">
                  <div class="content-wrap">
                    <article class="page-card">
                      {% if page.show_title != false %}
                      <header class="page-header{% if page.session_num %} page-header--session{% endif %}">
                        {% if page.collection_label %}
                        <p class="eyebrow">{{ page.collection_label }}</p>
                        {% endif %}
                        {% if page.session_num %}
                        <div class="session-chapter-nav" aria-label="Navigazione tra sessioni">
                          {% if page.session_nav_prev_route %}
                          <a class="session-chapter-nav__link session-chapter-nav__link--prev" href="{{ page.session_nav_prev_route | relative_url }}" title="{{ page.session_nav_prev_title | escape }}">
                            <span class="session-chapter-nav__arrow" aria-hidden="true">←</span>
                            <span class="session-chapter-nav__text">{{ page.session_nav_prev_label }}</span>
                          </a>
                          {% else %}
                          <span class="session-chapter-nav__spacer" aria-hidden="true"></span>
                          {% endif %}
                          <h1>{{ page.title }}</h1>
                          {% if page.session_nav_next_route %}
                          <a class="session-chapter-nav__link session-chapter-nav__link--next" href="{{ page.session_nav_next_route | relative_url }}" title="{{ page.session_nav_next_title | escape }}">
                            <span class="session-chapter-nav__text">{{ page.session_nav_next_label }}</span>
                            <span class="session-chapter-nav__arrow" aria-hidden="true">→</span>
                          </a>
                          {% else %}
                          <span class="session-chapter-nav__spacer" aria-hidden="true"></span>
                          {% endif %}
                        </div>
                        {% else %}
                        <div class="page-header-title-row">
                          <h1>{{ page.title }}</h1>
                          {% if page.start_reading_route %}
                          <a class="page-header-start-reading" href="{{ page.start_reading_route | relative_url }}">Comincia la lettura</a>
                          {% endif %}
                        </div>
                        {% endif %}
                      </header>
                      {% endif %}
                      <div class="page-content">
                        {{ content }}
                      </div>
                    </article>
                  </div>
                </main>
              </div>
            </div>
            <script src="{{ '/assets/site.js' | relative_url }}" defer></script>
          </body>
        </html>
        """
    ).replace(
        "@HEADER_LOGO_LIQUID@",
        "{{ '" + HEADER_LOGO_PUBLIC_PATH + "' | relative_url }}",
    )
    (layout_dir / "default.html").write_text(layout_text, encoding="utf-8")


def front_matter(
    title: str,
    route: str,
    collection_label: str,
    source_path: Path,
    *,
    show_title: bool = True,
    og_image: str | None = None,
    hero_image: str | None = None,
    home_full_bleed: bool = False,
    png_hub: bool = False,
    session_num: int | None = None,
    session_nav_prev: SessionNavLink | None = None,
    session_nav_next: SessionNavLink | None = None,
    start_reading_route: str | None = None,
) -> str:
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        'layout: "default"',
        f"permalink: {yaml_string(route)}",
        f"collection_label: {yaml_string(collection_label)}",
        f"source_path: {yaml_string(source_path.as_posix())}",
    ]
    if png_hub:
        lines.append("png_hub: true")
    if not show_title:
        lines.append("show_title: false")
    if og_image:
        lines.append(f"og_image: {yaml_string(og_image)}")
    if hero_image:
        lines.append(f"hero_image: {yaml_string(hero_image)}")
    if home_full_bleed:
        lines.append("home_full_bleed: true")
    if session_num is not None:
        lines.append(f"session_num: {session_num}")
    if session_nav_prev:
        lines.append(f"session_nav_prev_route: {yaml_string(session_nav_prev.route)}")
        lines.append(f"session_nav_prev_label: {yaml_string(session_nav_prev.label)}")
        lines.append(f"session_nav_prev_title: {yaml_string(session_nav_prev.title_attr)}")
    if session_nav_next:
        lines.append(f"session_nav_next_route: {yaml_string(session_nav_next.route)}")
        lines.append(f"session_nav_next_label: {yaml_string(session_nav_next.label)}")
        lines.append(f"session_nav_next_title: {yaml_string(session_nav_next.title_attr)}")
    if start_reading_route:
        lines.append(f"start_reading_route: {yaml_string(start_reading_route)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_index(manifest: dict, pages: list[PageEntry]) -> str:
    home_pages = [page for page in pages if public_sidebar_section(page) is None]
    featured_pages = [page for page in home_pages if page.featured]
    other_pages = [page for page in home_pages if not page.featured]

    hero_img = "{{ '" + HOME_HERO_PUBLIC_PATH + "' | relative_url }}"
    lines = [
        front_matter(
            title=manifest["site"]["title"],
            route="/",
            collection_label="Archivio pubblico",
            source_path=Path("tools/pubblicazione/manifest.json"),
            show_title=False,
            og_image=HOME_HERO_PUBLIC_PATH,
        ),
        "",
        f'<h1 class="home-tagline">{html.escape(manifest["site"]["tagline"])}</h1>',
        "",
        '<div class="hero">',
        f"{manifest['site']['description']}",
        "</div>",
        f'<figure class="home-hero"><img src="{hero_img}" alt="Il gruppo di avventurieri in carovana" loading="eager" decoding="async"></figure>',
    ]

    if featured_pages:
        lines.extend(["", "## Percorsi consigliati", ""])
        for page in featured_pages:
            lines.append(f"- [{page.label}]({{{{ '{page.route}' | relative_url }}}})")

    if other_pages:
        lines.extend(["", "## Altri contenuti player-safe", ""])
        for page in other_pages:
            lines.append(f"- [{page.title}]({{{{ '{page.route}' | relative_url }}}})")

    return "\n".join(lines).strip() + "\n"
