from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dash import dcc
import dash_mantine_components as dmc


# ----------------------------
# Cache control
# ----------------------------


def _md_cache_enabled() -> bool:
    v = os.getenv("MD_CACHE", "1").strip().lower()
    return v not in {"0", "false", "no", "off"}


@lru_cache(maxsize=256)
def _read_text_cached(abs_path: str) -> str:
    return Path(abs_path).read_text(encoding="utf-8")


def read_md(caller_file: str, relative_path: str) -> str:
    base_dir = Path(caller_file).resolve().parent
    abs_path = (base_dir / relative_path).resolve()

    if not abs_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found:\n  {abs_path}\n"
            f"(caller: {caller_file}, relative: {relative_path})"
        )

    if _md_cache_enabled():
        return _read_text_cached(str(abs_path))
    else:
        return abs_path.read_text(encoding="utf-8")


# ----------------------------
# Rendering helper
# ----------------------------


def render_md_section(
    caller_file: str,
    relative_path: str,
    *,
    size: str = "sm",
    class_name: str = "article-md",
):
    """
    Render a markdown section with Mantine typography styles.

    Example:
        render_md_section(__file__, "sections/01_intro.md")
    """
    md_text = read_md(caller_file, relative_path)

    return dmc.Container(
        size=size,
        children=dmc.TypographyStylesProvider(
            dcc.Markdown(md_text, className=class_name)
        ),
    )
