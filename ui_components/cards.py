from __future__ import annotations

from typing import Optional, Sequence, Tuple, Any

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify


# ----------------------------
# Graph card builder
# ----------------------------


def graph_card(
    *children,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    right: Optional[Any] = None,
    help_icon: Optional[Any] = None,
    my: str = "md",
    with_border: bool = True,
    shadow: str = "sm",
    radius: str = "md",
    body_gap: str = "xs",
    **kwargs,
):
    """
    Consistent wrapper for cards that primarily host a graph + small header copy.

    Usage:
        graph_card(
            dcc.Graph(...),
            title="Monthly Temperature Profiles Across the Record",
            subtitle="Each line represents a year ...",
            right=some_controls_group,
        )
    """
    header_children = []
    if title:
        title_row = [dmc.Title(title, order=2)]
        if help_icon is not None:
            title_row.append(help_icon)

        header_children.append(dmc.Group(gap="xs", align="center", children=title_row))

    header = None
    if right is not None or header_children:
        header = dmc.Group(
            justify="space-between",
            align="center",
            children=[
                (
                    dmc.Stack(gap=2, children=header_children)
                    if header_children
                    else dmc.Box()
                ),
                right if right is not None else dmc.Box(),
            ],
        )

    body_children = []
    if header is not None:
        body_children.append(header)

    if subtitle:
        body_children.append(dmc.Text(subtitle, size="sm", c="dimmed"))

    body_children.extend(children)

    return dmc.Card(
        withBorder=with_border,
        shadow=shadow,
        radius=radius,
        my=my,
        children=dmc.Stack(gap=body_gap, children=body_children),
        **kwargs,
    )


# ----------------------------
# Footer helpers
# ----------------------------


def iconify(icon_name: str, *, size: int = 18) -> Any:
    """
    Central icon factory. If you ever change icon sets or sizes, do it here.

    Note: Iconify usually won't raise if the icon name is wrong — it will just
    fail to render the glyph. Keeping icon names in one place is the best
    defence.
    """
    return DashIconify(icon=icon_name, width=size, height=size)


def external_link_item(
    label: str,
    href: str,
    *,
    icon: Optional[Any] = None,
    underline: str = "hover",
) -> Any:
    """
    External link rendered as <a> for full control over rel/target,
    while keeping Mantine styling inside.
    """
    content = dmc.Group(
        gap=6,
        children=[
            icon if icon is not None else None,
            dmc.Text(label, span=True),
        ],
    )

    # Use Mantine's underline styling by applying it to the Text via mod/data attribute
    # (Anchor would do this automatically, but we can't reliably pass rel there).
    # For now, keep it simple: let browser handle underline on hover via CSS or omit.
    # If you want true Mantine underline behavior later, we can add a small CSS rule.

    return html.A(
        content,
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        style={
            "textDecoration": "none"
        },  # keep the layout clean; rely on styling later if desired
    )


def page_footer(
    *,
    github_url: str,
    linkedin_url: str,
    related_links: Optional[Sequence[Tuple[str, str]]] = None,
    next_page: Optional[Tuple[str, str]] = None,
    note: Optional[str] = None,
    my: str = "lg",
    with_border: bool = True,
    shadow: str = "sm",
    radius: str = "md",
) -> Any:
    identity = dmc.Group(
        gap="lg",
        children=[
            external_link_item(
                "GitHub", github_url, icon=iconify("tabler:brand-github")
            ),
            external_link_item(
                "LinkedIn", linkedin_url, icon=iconify("tabler:brand-linkedin")
            ),
        ],
    )

    related = None
    if related_links:
        related_items = [
            external_link_item(label, url, icon=iconify("tabler:external-link"))
            for label, url in related_links
        ]
        related = dmc.Stack(
            gap=6,
            children=[
                dmc.Text("Related", fw=600, size="sm"),
                dmc.Stack(gap=6, children=related_items),
            ],
        )

    # Desktop "Next" (normal)
    next_btn_desktop = None
    # Mobile "Next" (full width)
    next_btn_mobile = None

    if next_page:
        next_label, next_href = next_page

        next_btn_desktop = dcc.Link(
            dmc.Button(
                next_label,
                variant="light",
                rightSection=iconify("tabler:arrow-right"),
            ),
            href=next_href,
            style={"textDecoration": "none"},
        )

        next_btn_mobile = dcc.Link(
            dmc.Button(
                next_label,
                variant="light",
                rightSection=iconify("tabler:arrow-right"),
                fullWidth=True,
            ),
            href=next_href,
            style={"textDecoration": "none", "width": "100%"},
        )

    about_block = dmc.Stack(
        gap=8,
        children=[
            dmc.Text("About this project", fw=600),
            dmc.Text(
                note
                or "An independent, data-first visual exploration of measured UK temperature records.",
                size="sm",
                c="dimmed",
            ),
            identity,
        ],
    )

    # Desktop layout: two columns (about on left, related + next on right)
    desktop_layout = dmc.Group(
        justify="space-between",
        align="flex-start",
        visibleFrom="sm",
        children=[
            about_block,
            dmc.Group(
                gap="xl",
                align="flex-start",
                children=[x for x in (related, next_btn_desktop) if x is not None],
            ),
        ],
    )

    # Mobile layout: stacked, with clear reading order
    mobile_layout = dmc.Stack(
        gap="md",
        hiddenFrom="sm",
        children=[
            about_block,
            related if related is not None else dmc.Box(),
            next_btn_mobile if next_btn_mobile is not None else dmc.Box(),
        ],
    )

    return dmc.Card(
        withBorder=with_border,
        shadow=shadow,
        radius=radius,
        my=my,
        children=[
            desktop_layout,
            mobile_layout,
        ],
    )
