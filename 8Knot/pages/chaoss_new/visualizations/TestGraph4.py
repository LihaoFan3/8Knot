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
import math
import numpy as np
from datetime import date


PAGE = "chaoss"
VIZ_ID = "TestGraph0_name_test_Graph4"

TestGraph4 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "TestGraph4",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This visualization gives a view into the development speed of a repository in\n
                            relation to the other selected repositories. For more context of this visualization see\n
                            https://chaoss.community/kb/metric-project-velocity/ \n
                            https://www.cncf.io/blog/2017/06/05/30-highest-velocity-open-source-projects/ """
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
                        # dbc.Row(
                        #     [
                        #         dbc.Label(
                        #             "Issue Opened Weight:",
                        #             html_for=f"issue-opened-weight-{PAGE}-{VIZ_ID}",
                        #             width={"size": "auto"},
                        #         ),
                        #         dbc.Col(
                        #             dbc.Input(
                        #                 id=f"issue-opened-weight-{PAGE}-{VIZ_ID}",
                        #                 type="number",
                        #                 min=0,
                        #                 max=1,
                        #                 step=0.1,
                        #                 value=0.3,
                        #                 size="sm",
                        #             ),
                        #             className="me-2",
                        #             width=1,
                        #         ),
                        #         dbc.Label(
                        #             "Issue Closed Weight:",
                        #             html_for=f"issue-closed-weight-{PAGE}-{VIZ_ID}",
                        #             width={"size": "auto"},
                        #         ),
                        #         dbc.Col(
                        #             dbc.Input(
                        #                 id=f"issue-closed-weight-{PAGE}-{VIZ_ID}",
                        #                 type="number",
                        #                 min=0,
                        #                 max=1,
                        #                 step=0.1,
                        #                 value=0.4,
                        #                 size="sm",
                        #             ),
                        #             className="me-2",
                        #             width=1,
                        #         ),
                        #         dbc.Label(
                        #             "Y-axis:",
                        #             html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                        #             width="auto",
                        #         ),
                        #         dbc.Col(
                        #             dbc.RadioItems(
                        #                 id=f"graph-view-{PAGE}-{VIZ_ID}",
                        #                 options=[
                        #                     {"label": "Non-log", "value": False},
                        #                     {"label": "Log", "value": True},
                        #                 ],
                        #                 value=False,
                        #                 inline=True,
                        #             ),
                        #             className="me-2",
                        #         ),
                        #     ],
                        #     align="center",
                        # ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    # dcc.DatePickerRange(
                                    #     id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                    #     min_date_allowed=dt.date(2005, 1, 1),
                                    #     max_date_allowed=dt.date.today(),
                                    #     initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                    #     clearable=True,
                                    # ),
                                     dcc.DatePickerSingle(
                                        id='my-date-picker-single',
                                        min_date_allowed=date(1995, 8, 5),
                                        max_date_allowed=date(2023, 12, 31),
                                        initial_visible_month=date(2023, 8, 10),
                                        date=date(2023, 8, 10)
                                        ),
                                    width="auto",
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
                            justify="between",
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
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_op   en")],
)
def toggle_popover4(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for Project Velocity graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        # Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"issue-opened-weight-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"issue-closed-weight-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"pr-open-weight-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"pr-merged-weight-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"pr-closed-weight-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        Input('my-date-picker-single', 'date'),
    ],
    background=True,
)
def project_velocity_graph4(
    # repolist, log, i_o_weight, i_c_weight, pr_o_weight, pr_m_weight, pr_c_weight, start_date, end_date
    repolist, end_date
):

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
        return nodata_graph

    # function for all data pre processing
    df = process_data(df, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(
    df: pd.DataFrame,
    end_date,
):

    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # filter values based on date picker
    if end_date is not None:
        df = df[df.created_at <= end_date]

    # df to hold value of unique contributors for each repo
    df_cntrbs = pd.DataFrame(df.groupby("repo_name")["cntrb_id"].nunique()).rename(
        columns={"cntrb_id": "num_unique_contributors"}
    )

    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    # print("_______________________-testGraph4")
    closedNumberList=[]
    openedNumberList=[]
    dateList=[]
    firstLine=df.iloc[0:1]
    lastLine=df.tail(1)
    fYear=firstLine['created_at'].iloc[0].year
    fMonth=firstLine['created_at'].iloc[0].month
    lYear=lastLine['created_at'].iloc[0].year
    lMonth=lastLine['created_at'].iloc[0].month
    if fYear<(lYear-1):
        fYear=lYear-1
    # print("___________________________________getin 0 ")
    residualOpen=0
    for yearCur in range(fYear,lYear+1):
        monthStart=1
        monthEnd=12
        # print("___________________________________getin 0 ")
        if yearCur==lYear:
            monthEnd=lMonth
        if yearCur==fYear:
            monthStart=fMonth
        for monthCur in range(monthStart,monthEnd+1):
            opendNumberMonth=0
            closedNumberMonth=0
            mergedNumberMonth=0
            yearNex = yearCur
            monthNex =monthCur+1
            # print("___________________________________getin 1 ")
            if monthCur==12:
                    monthNex=1
                    yearNex=yearCur+1
            # print("___________________________________getin2 ")
            ts = pd.to_datetime(str(yearCur) + "-" + str(monthCur),utc=True)
            # print(type(ts))
            tsNext=pd.to_datetime(str(yearNex) + "-" + str(monthNex),utc=True)
            dfCur=df.loc[(df['created_at']>ts)&(df['created_at']<tsNext)]
            # print("___________________________________getin3 ")
            # print(dfCur)
            opendNumberMonth=len(dfCur.loc[df['Action'] =='PR Opened'])+residualOpen
            closedNumberMonth=len(dfCur.loc[df['Action']=='PR Closed'])
            mergedNumberMonth=len(dfCur.loc[df['Action']=='PR Merged'])    
            closedAndMerged=closedNumberMonth+mergedNumberMonth
            residualOpen=opendNumberMonth-closedAndMerged
            closedNumberList.append(closedAndMerged)    
            openedNumberList.append(opendNumberMonth)
            dateCur=str(yearCur) + "-" + str(monthCur)
            dateList.append(dateCur)
            # print("openddNumber=",end='')
            # print(opendNumberMonth)
            # print("closed and merged=",end="")
            # print(closedAndMerged)
            # print("closedNumber=",end='')
            # print(closedNumberMonth)
            # print("mergeddNumber=",end='')
            # print(mergedNumberMonth)
            # print("_________________________")
            # print("_________________________")
            # print("_________________________")
            # print("_________________________")
            # print("_________________________")
            # print("_________________________")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    print("_______________________-testGraph4")
    data = {'date':dateList,
       'opened PR':openedNumberList,
       'closed PR':closedNumberList}
    df=pd.DataFrame(data)
    print(len(df['date']))
    print(len(df['opened PR']))
    print(len(df['closed PR']))
    return df


def create_figure(df: pd.DataFrame):
    print("____________________________getin—___createFigure")
    print("____________________________getin—___createFigure")
    print("____________________________getin—___createFigure")
    print("____________________________getin—___createFigure")
    print("____________________________getin—___createFigure")
    print("____________________________getin—___createFigure")
    print(len(df['date']))
    print(len(df['opened PR']))
    print(len(df['closed PR']))
    print("____________________________getin_______df___output")
    print("____________________________getin_______df___output")
    print("____________________________getin_______df___output")
    print("____________________________getin_______df___output")
    color_seq = [
        "#B5B682",  # sage
        "#c0bc5d",  # citron (yellow-ish)
        "#6C8975",  # reseda green
        "#D9AE8E",  # buff (pale pink)
        "#FFBF51",  # xanthous (orange-ish)
        "#C7A5A5",  # rosy brown
    ]
    fig = px.line(df, x='date', y=['opened PR', 'closed PR'],color_discrete_sequence=color_seq)
    print("____________________________getin_0")
    print("____________________________getin_0")
    print("____________________________getin_0")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="open PR & closed PR",
        margin_b=40,
        font=dict(size=14),
        legend_title="Repo Name",
    )
    print("____________________________getin_1")
    print("____________________________getin_1")
    print("____________________________getin_1")
    

    # y_axis = "prs_issues_actions_weighted"
    # y_title = "Weighted PR/Issue Actions"
    # if log:
    #     y_axis = "log_prs_issues_actions_weighted"
    #     y_title = "Log of Weighted PR/Issue Actions"

    # # graph generation
    # fig = px.scatter(
    #     df,
    #     x="log_num_commits",
    #     y=y_axis,
    #     color="repo_name",
    #     size="log_num_contrib",
    #     hover_data=["repo_name", "Commit", "PR Opened", "Issue Opened", "num_unique_contributors"],
    #     color_discrete_sequence=color_seq,
    # )

    # fig.update_traces(
    #     hovertemplate="Repo: %{customdata[0]} <br>Commits: %{customdata[1]} <br>Total PRs: %{customdata[2]}"
    #     + "<br>Total Issues: %{customdata[3]} <br>Total Contributors: %{customdata[4]}<br><extra></extra>",
    # )

    # # layout styling
    # fig.update_layout(
    #     xaxis_title="Logarithmic Commits",
    #     yaxis_title=y_title,
    #     margin_b=40,
    #     font=dict(size=14),
    #     legend_title="Repo Name",
    # )

    return fig
