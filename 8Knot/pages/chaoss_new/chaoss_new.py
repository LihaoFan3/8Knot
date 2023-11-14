from dash import html, dcc
import dash 
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.TestGraph0 import TestGraph0
from .visualizations.TestGraph1 import TestGraph1

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chaoss_new")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(TestGraph0, width=6),
                dbc.Col(TestGraph1, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)