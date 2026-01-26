from dash import Output, Input, ctx, no_update
import dash_mantine_components as dmc

from pages.overview.page import get_overview_layout
from pages.exceptional.page import get_exceptional_layout
from pages.winter.page import get_winter_layout
from pages.methodology.page import get_methodology_layout
from app_core.view_range import get_view_range, set_view_range

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

        if section == "method":
            return get_methodology_layout(df_cet)

        return dmc.Card(
            withBorder=True,
            shadow="sm",
            radius="md",
            children=[
                dmc.Title("Page not found", order=2),
                dmc.Text("Something went wrong, sorry!", c="dimmed"),
            ],
        )


def register_view_range_callbacks(app, df_cet):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    def _range_from_preset(preset: str) -> tuple[int, int]:
        if preset == "modern":
            return max(1950, min_year), max_year
        if preset == "instrumental":
            return max(1772, min_year), max_year
        if preset == "full":
            return min_year, max_year
        return max(1950, min_year), max_year

    def _preset_from_range(start: int, end: int) -> str:
        if start == max(1950, min_year) and end == max_year:
            return "modern"
        if start == max(1772, min_year) and end == max_year:
            return "instrumental"
        if start == min_year and end == max_year:
            return "full"
        return "modern"

    @app.callback(
        Output("global-view-range", "data"),
        Output("global-range-preset", "value"),
        Input("global-range-preset", "value"),
        Input("global-view-range", "data"),
    )
    def sync_global_view_range(range_preset: str, view_range_data):
        trigger = ctx.triggered_id

        if trigger is None:
            view_range = get_view_range(
                view_range_data, min_year=min_year, max_year=max_year
            )
            if view_range.start_year == min_year and view_range.end_year == max_year:
                start, end = _range_from_preset("instrumental")
                view_range = set_view_range(
                    start, end, min_year=min_year, max_year=max_year
                )
                preset = _preset_from_range(
                    view_range["start_year"], view_range["end_year"]
                )
                return view_range, preset

            preset = _preset_from_range(view_range.start_year, view_range.end_year)
            return no_update, preset

        if trigger == "global-range-preset":
            start, end = _range_from_preset(range_preset)
            view_range = set_view_range(
                start, end, min_year=min_year, max_year=max_year
            )
            preset = _preset_from_range(
                view_range["start_year"], view_range["end_year"]
            )
            return view_range, preset

        if trigger == "global-view-range":
            view_range = get_view_range(
                view_range_data, min_year=min_year, max_year=max_year
            )
            preset = _preset_from_range(view_range.start_year, view_range.end_year)
            return no_update, preset

        return no_update, no_update
