from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as ctq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
from dash import dcc

"""
NOTE: VARIABLES TO CHANGE:

(1) PAGE
(2) VIZ_ID
(3) gc_VISUALIZATION
(4) TITLE OF VISUALIZATION
(5) CONTEXT OF GRAPH
(6) IDs of Dash components
(6) NAME_OF_VISUALIZATION_graph
(7) COLUMN_WITH_DATETIME
(8) COLUMN_WITH_DATETIME
(9) COLUMN_TO_SORT_BY
(10) Comments before callbacks
(11) QUERY_USED, QUERY_NAME, QUERY_INITIALS

NOTE: IMPORTING A VISUALIZATION INTO A PAGE
(1) Include the visualization file in the visualization folder for the respective page
(2) Import the visualization into the page_name.py file using "from .visualizations.visualization_file_name import gc_visualization_name"
(3) Add the card into a column in a row on the page

NOTE: ADDITIONAL DASH COMPONENTS FOR USER GRAPH CUSTOMIZATIONS

If you add Dash components (ie dbc.Input, dbc.RadioItems, dcc.DatePickerRange...) the ids, html_for, and targets should be in the
following format: f"component-identifier-{PAGE}-{VIZ_ID}"

NOTE: If you change or add a new query, you need to do "docker system prune -af" before building again

NOTE: If you use an alert or take code from a visualization that uses one, make sure to update returns accordingly in the NAME_OF_VISUALIZATION_graph

For more information, check out the new_vis_guidance.md
"""


# TODO: Remove unused imports and edit strings and variables in all CAPS
# TODO: Remove comments specific for the template

PAGE = "chaoss"
VIZ_ID = "contributor_count"

gc_contributor_count = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Count",
                    id=f"Contributor Count",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("This graph shows the number of contributors per month for a given range. It helps to highlight when the repository had the most traffic and support."),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Form(
                    [
                        # dbc.Row(
                            # [
                                # dbc.Label(
                                #     "Date Interval:",
                                #     html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                #     width="auto",
                                # ),
                                # dbc.Col(
                                #     [
                                #         dbc.RadioItems(
                                #             id=f"date-radio-{PAGE}-{VIZ_ID}",
                                #             options=[

                                #                 {"label": "Week","value": "W",},
                                #                 {"label": "Month", "value": "M"},
                                #                 {"label": "Year", "value": "Y"},
                                #             ],
                                #             value="M",
                                #             inline=True,
                                #         ),
                                #     ]
                                # ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dcc.DatePickerRange(
                                            id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                            min_date_allowed=dt.date(2005, 1, 1),
                                            max_date_allowed=dt.date.today(),
                                            initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                            clearable=True,
                                        ),
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "About Graph",
                                            id=f"popover-target-{PAGE}-{VIZ_ID}",
                                            color="secondary",
                                            size="sm",
                                        ),
                                    ],
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        # TODO: ADD IN IF ADDITIONAL PARAMETERS FOR GRAPH, REMOVE IF NOT
                        # """ format dbc.Inputs, including dbc.Alert if needed
                        #         dbc.Label(
                        #             "TITLE_OF_ADDITIONAL_PARAMETER:",
                        #             html_for=f"component-identifier-{PAGE}-{VIZ_ID}",
                        #             width={"size": "auto"},
                        #         ),
                        #         dbc.Col(
                        #             dbc.Input(
                        #                 id=f"component-identifier-{PAGE}-{VIZ_ID}",,
                        #                 type="number",
                        #                 min=1,
                        #                 max=120,
                        #                 step=1,
                        #                 value=7,
                        #             ),
                        #             className="me-2",
                        #             width=2,
                        #         ),
                        #         dbc.Alert(
                        #             children="Please ensure that 'PARAMETER' is less than 'PARAMETER'",
                        #             id=f"component-identifier-{PAGE}-{VIZ_ID}",
                        #             dismissable=True,
                        #             fade=False,
                        #             is_open=False,
                        #             color="warning",
                        #         ),
                        # """
                        # """ format for dcc.DatePickerRange:
                        # dbc.Col(
                        #     dcc.DatePickerRange(
                        #         id=f"date-range-{PAGE}-{VIZ_ID}",
                        #         min_date_allowed=dt.date(2005, 1, 1),
                        #         max_date_allowed=dt.date.today(),
                        #         clearable=True,
                        #     ),
                        #     width="auto",
                        # ),

                        # """,
                    ]
                ),
            ]
        )
    ],
)

# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

# callback for date range changed and graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)

def contributor_count_graph(repolist, start_date, end_date):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # function for all data pre processing
    df = process_data(df, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    
    return fig

# Need to determine number of contributors per month
def process_data(df: pd.DataFrame, start_date, end_date):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # Process the DataFrame
    # Convert 'created_at' column to datetime and sort by date. 
    # Filter start_date and end_date.
    df = (
        df.assign(created_at=pd.to_datetime(df['created_at'], utc=True))
        .sort_values(by='created_at')
        .pipe(lambda x: x[x.created_at >= start_date] if start_date is not None else x)
        .pipe(lambda x: x[x.created_at <= end_date] if end_date is not None else x)
        .assign(month=lambda x: x['created_at'].dt.to_period('M'))
    )

    # Count unique contributors per month
    monthly_contributors = df.groupby('month')['cntrb_id'].nunique().reset_index(name='contrib_num')
    monthly_contributors['month'] = monthly_contributors['month'].dt.to_timestamp()

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    return monthly_contributors


def create_figure(df: pd.DataFrame):
    # Graph generation
    fig = px.bar(
        df,
        x="month",
        y="contrib_num",
        color="contrib_num",
        color_continuous_scale="Viridis"
    )

    # Layout customization
    fig.update_layout(
        title="Contributor Count by Month",
        xaxis_title="Month",
        yaxis_title="Number of Contributors",
        legend_title="Number of Contributors",
        coloraxis_colorbar=dict(title="Number of Contributors")
    )

    return fig