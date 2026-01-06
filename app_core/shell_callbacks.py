from dash import Output, Input, State, ctx, no_update
import dash_mantine_components as dmc


from pages.overview.page import get_overview_layout
# later:
# from pages.exceptional.page import get_exceptional_layout
# from pages.winter.page import get_winter_layout
# from pages.rainfall.page import get_rainfall_layout
# from pages.methodology.page import get_methodology_layout


def register_shell_callbacks(app, df_cet):
    @app.callback(
        Output("nav-section-store", "data"),
        Output("nav-tabs", "value"),
        Output("nav-select", "value"),
        Input("nav-tabs", "value"),
        Input("nav-select", "value"),
        State("nav-section-store", "data"),
        prevent_initial_call=False,
    )
    def sync_nav(tab_value, select_value, current):
        trig = ctx.triggered_id

        if trig == "nav-tabs" and tab_value:
            chosen = tab_value
        elif trig == "nav-select" and select_value:
            chosen = select_value
        else:
            # initial load or weird edge: fall back to stored value
            chosen = current or "overview"

        # keep all three aligned
        return chosen, chosen, chosen

def register_page_router_callback(app, df_cet):
    @app.callback(
        Output("page-content", "children"),
        Input("nav-section-store", "data"),
    )
    def render_page(section: str):
        if section == "overview":
            return get_overview_layout(df_cet)

        # placeholders for now
        title_map = {
            "exceptional": "Exceptional Months",
            "winter": "Winter in Focus",
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