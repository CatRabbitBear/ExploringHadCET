from __future__ import annotations

import dash_mantine_components as dmc

SKELETON_2D_ID = "overview-skeleton-2d"
SKELETON_3D_ID = "overview-skeleton-3d"
PAGE_SKELETON_OVERLAY_ID = "overview-page-skeleton-overlay"


PAGE_SKELETON_VISIBLE_STYLE = {
    "position": "absolute",
    "inset": 0,
    "zIndex": 20,
    "background": "var(--mantine-color-body)",
}

PAGE_SKELETON_HIDDEN_STYLE = {
    "display": "none",
}


def wrap_overview_2d_skeleton(child):
    return dmc.Skeleton(
        id=SKELETON_2D_ID,
        visible=True,
        radius="md",
        style={"height": "var(--graph-height-2d)"},
        children=child,
    )


def wrap_overview_3d_skeleton(child):
    return dmc.Skeleton(
        id=SKELETON_3D_ID,
        visible=True,
        radius="md",
        style={"height": "var(--graph-height-3d)"},
        children=child,
    )


def build_overview_page_skeleton_overlay():
    return dmc.Box(
        id=PAGE_SKELETON_OVERLAY_ID,
        style=PAGE_SKELETON_VISIBLE_STYLE,
        children=dmc.Stack(
            gap="md",
            children=[
                dmc.Skeleton(visible=True, radius="sm", style={"height": 34}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 26}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 180}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 640}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 140}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 780}),
                dmc.Skeleton(visible=True, radius="sm", style={"height": 140}),
                dmc.Skeleton(visible=True, radius="md", style={"height": 220}),
            ],
        ),
    )
