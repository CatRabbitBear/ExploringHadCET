from dash import dcc
import dash_mantine_components as dmc
import pandas as pd

from pages.markdown_utils import render_md_section
from ui_components.cards import page_footer


def get_methodology_layout(df_cet: pd.DataFrame):

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title("Methodology", order=2, ta="center"),
            # dmc.Title(
            #     "Comparing December, January, and February across the historical record.",
            #     order=3,
            #     ta="center",
            # ),
            render_md_section(__file__, "sections/01_intro.md"),
            render_md_section(__file__, "sections/02_discussion.md"),
            page_footer(
                github_url="https://github.com/CatRabbitBear/UKClimateDashboard",
                linkedin_url="https://www.linkedin.com/in/anthony-cokayne-34a719356/",
                related_links=[
                    (
                        "Met Office HadCET data",
                        "https://www.metoffice.gov.uk/hadobs/hadcet/data/download.html",
                    ),
                ],
                next_page=None,
            ),
        ],
    )
