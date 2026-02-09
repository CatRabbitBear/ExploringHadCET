from __future__ import annotations

import dash_mantine_components as dmc

PAGE_SKELETON_OVERLAY_ID = "exceptional-page-skeleton-overlay"

PAGE_SKELETON_VISIBLE_STYLE = {
    "position": "absolute",
    "inset": 0,
    "zIndex": 20,
    "background": "var(--mantine-color-body)",
}

PAGE_SKELETON_HIDDEN_STYLE = {
    "display": "none",
}


def build_exceptional_page_skeleton_overlay():
    return dmc.Box(
        id=PAGE_SKELETON_OVERLAY_ID,
        style=PAGE_SKELETON_VISIBLE_STYLE,
        children=dmc.Stack(
            gap="md",
            children=[
                dmc.Skeleton(visible=True, radius="sm", style={"height": 34}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 26}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 180}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 160}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 420}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 420}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 140}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 220}),
            ],
        ),
    )
