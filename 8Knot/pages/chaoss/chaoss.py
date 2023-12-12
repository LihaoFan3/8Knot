from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.project_velocity import gc_project_velocity
from .visualizations.contrib_importance_pie import gc_contrib_importance_pie
from .visualizations.release_frequency import gc_RELEASE_FREQUENCY
from .visualizations.commit_frequency import gc_COMMIT_FREQUENCY

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chaoss")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_contrib_importance_pie, width=6),
                dbc.Col(gc_project_velocity, width=6),
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
        )
    ],
    fluid=True,
)
