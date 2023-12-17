from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.close_ratio import gc_close_ratio
from .visualizations.contrib_importance_pie import gc_contrib_importance_pie
from .visualizations.release_frequency import gc_RELEASE_FREQUENCY
from .visualizations.commit_frequency import gc_COMMIT_FREQUENCY
from .visualizations.bus_factor import gc_bus_factor
from .visualizations.contributor_count import gc_contributor_count

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chaoss")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_contrib_importance_pie, width=6),
                dbc.Col(gc_close_ratio, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"}
            ),

        dbc.Row(
            [
                dbc.Col(gc_RELEASE_FREQUENCY, width=6),
                dbc.Col(gc_COMMIT_FREQUENCY, width=6)
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_bus_factor, width=6),
                dbc.Col(gc_contributor_count, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"}
            )
    ],
    fluid=True,
)
