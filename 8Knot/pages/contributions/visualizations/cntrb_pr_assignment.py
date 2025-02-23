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
from queries.pr_assignee_query import pr_assignee_query as praq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import app

PAGE = "contributions"
VIZ_ID = "cntrib-pr-assignment"

gc_cntrib_pr_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Pull Request Review Assignment",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes number of pull request reviews assigned to each each contributor\n
                            in the specifed time bucket. The visualization only includes contributors\n
                            that meet the user inputed the assignment criteria.
                            """
                        ),
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
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Total Assignments Required:",
                                    html_for=f"assignments-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"assignments-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=250,
                                        step=1,
                                        value=10,
                                        size="sm",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Alert(
                                    children="No contributors meet assignment requirement",
                                    id=f"check-alert-{PAGE}-{VIZ_ID}",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Week", "value": "W"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="W",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
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


# callback for pull request review assignment graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input(f"assignments-required-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def cntrib_pr_assignment_graph(repolist, interval, assign_req, bot_switch):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=praq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=praq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # remove bot data
    if bot_switch:
        df = df[~df["assignee"].isin(app.bots_list)]

    df = process_data(df, interval, assign_req)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, assign_req):

    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)
    df["assign_date"] = pd.to_datetime(df["assign_date"], utc=True)

    # order values chronologically by created date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # drop all issues that have no assignments
    df = df[~df.assignment_action.isnull()]

    # df of rows that are assignments
    df_contrib = df[df["assignment_action"] == "assigned"]

    # count the assignments total for each contributor
    df_contrib = (
        df_contrib["assignee"]
        .value_counts()
        .to_frame()
        .reset_index()
        .rename(columns={"assignee": "count", "index": "assignee"})
    )

    # create list of all contributors that meet the assignment requirement
    contributors = df_contrib["assignee"][df_contrib["count"] >= assign_req].to_list()

    # no update if there are not any contributors that meet the criteria
    if len(contributors) == 0:
        return dash.no_update, True

    # only include contributors that meet the criteria
    df = df.loc[df["assignee"].isin(contributors)]

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created"].min()
    latest = max(df["created"].max(), df["closed"].max())

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    # df for pull request review assignments in date intervals
    df_assign = dates.to_frame(index=False, name="start_date")

    # offset end date column by interval
    if interval == "D":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(days=1)
    elif interval == "W":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(weeks=1)
    elif interval == "M":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(months=1)
    else:
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(years=1)

    # iterates through contributors and dates for assignment values
    for contrib in contributors:
        df_assign[contrib] = df_assign.apply(
            lambda row: pr_assignment(df, row.start_date, row.end_date, contrib),
            axis=1,
        )

    # formatting for graph generation
    if interval == "M":
        df_assign["start_date"] = df_assign["start_date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_assign["start_date"] = df_assign["start_date"].dt.year

    return df_assign


def create_figure(df: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # list of contributors for plot
    contribs = df.columns.tolist()[2:]

    # making a line graph if the bin-size is small enough.
    if interval == "D":

        # list of lines for plot
        lines = []

        # iterate through colors for lines
        marker_val = 0

        # loop to create lines for each contributors
        for contrib in contribs:
            line = go.Scatter(
                name=contrib,
                x=df["start_date"],
                y=df[contrib],
                mode="lines",
                showlegend=True,
                hovertemplate="PRs Assigned: %{y}<br>%{x|%b %d, %Y}",
                marker=dict(color=color_seq[marker_val]),
            )
            lines.append(line)
            marker_val = (marker_val + 1) % 6
        fig = go.Figure(lines)
    else:
        fig = px.bar(
            df,
            x="start_date",
            y=contribs,
            color_discrete_sequence=color_seq,
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Prs Assigned: %{y}<br>")

        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=period,
            rangeslider_yaxis_rangemode="match",
            range=x_r,
        )

    # layout specifics for both styles of plots
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="PR Review Assignments",
        legend_title="Contributor ID",
        font=dict(size=14),
    )

    return fig


def pr_assignment(df, start_date, end_date, contrib):
    """
    This function takes a start and an end date and determines how many
    prs that are open during that time interval and are currently assigned
    to the contributor.

    Args:
    -----
        df : Pandas Dataframe
            Dataframe with issue assignment actions of the assignees

        start_date : Datetime Timestamp
            Timestamp of the start time of the time interval

        end_date : Datetime Timestamp
            Timestamp of the end time of the time interval

        contrib : str
            contrb_id for the contributor

    Returns:
    --------
        int: Number of assignments to the contributor in the time window
    """

    # drop rows not by contrib
    df = df[df["assignee"] == contrib]

    # drop rows that are more recent than the end date
    df_created = df[df["created"] <= end_date]

    # Keep issues that were either still open after the 'start_date' or that have not been closed.
    df_in_range = df_created[(df_created["closed"] > start_date) | (df_created["closed"].isnull())]

    # get all issue unassignments and drop rows that have been unassigned more recent than the end date
    df_unassign = df_in_range[
        (df_in_range["assignment_action"] == "unassigned") & (df_in_range["assign_date"] <= end_date)
    ]

    # get all issue assignments and drop rows that have been assigned more recent than the end date
    df_assigned = df_in_range[
        (df_in_range["assignment_action"] == "assigned") & (df_in_range["assign_date"] <= end_date)
    ]

    # return the different of assignments and unassignments
    return df_assigned.shape[0] - df_unassign.shape[0]
