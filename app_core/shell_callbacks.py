from dash import Output, Input, State, ctx, no_update
import dash_mantine_components as dmc

from pages.overview.page import get_overview_layout
from pages.exceptional.page import get_exceptional_layout
from pages.winter.page import get_winter_layout

# later:
# from pages.rainfall.page import get_rainfall_layout
# from pages.methodology.page import get_methodology_layout


VALID_SECTIONS = {"overview", "exceptional", "winter", "rainfall", "method"}


def _section_from_path(pathname: str | None) -> str:
    if not pathname or pathname == "/":
        return "overview"
    # "/overview" -> "overview"
    s = pathname.strip("/").split("/")[0].strip()
    return s if s in VALID_SECTIONS else "overview"


def _path_from_section(section: str) -> str:
    if section not in VALID_SECTIONS:
        section = "overview"
    return f"/{section}"


def register_shell_callbacks(app, df_cet):
    # 1) UI -> URL (user clicks tabs or dropdown)
    @app.callback(
        Output("url", "pathname"),
        Input("nav-tabs", "value"),
        Input("nav-select", "value"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def nav_to_url(tab_value, select_value, current_pathname):
        trig = ctx.triggered_id

        if trig == "nav-tabs" and tab_value:
            desired = _path_from_section(tab_value)
        elif trig == "nav-select" and select_value:
            desired = _path_from_section(select_value)
        else:
            return no_update

        # 🔑 Break the dependency cycle: if we're already at that URL, do nothing
        if current_pathname == desired:
            return no_update

        return desired

    # 2) URL -> UI (sync controls on refresh/back/share link)
    @app.callback(
        Output("nav-tabs", "value"),
        Output("nav-select", "value"),
        Input("url", "pathname"),
    )
    def url_to_nav(pathname):
        section = _section_from_path(pathname)
        return section, section

def register_page_router_callback(app, df_cet):
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
    )
    def render_page(pathname: str):
        section = _section_from_path(pathname)

        if section == "overview":
            return get_overview_layout(df_cet)

        if section == "exceptional":
            return get_exceptional_layout(df_cet)

        if section == "winter":
            return get_winter_layout(df_cet)

        title_map = {
            # "exceptional": "Exceptional Months",
            # "winter": "Winter in Focus",
            "rainfall": "Monthly Rainfall",
            "method": "Methodology",
        }
        return dmc.Card(
            withBorder=True,
            shadow="sm",
            radius="md",
            children=[
                dmc.Title(title_map.get(section, "Coming soon"), order=2),
                dmc.Text("Page stub — we’ll build this next.", c="dimmed"),
            ],
        )