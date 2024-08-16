"""
Plots to do:
Normalised ethnicity breakdown vs national results
Plot national age/gender breakdown on age plot
"""

import pandas as pd
import js
from js import files, postcode_data
import pyodide_js
import json
import io
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import openpyxl

import warnings
from pandas.core.common import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

# Initial variables
try:
    ref_date = pd.to_datetime(refDateVal, format="%Y-%m-%d")

    days_to_ref_date = pd.to_datetime("today") - ref_date
    days_to_ref_date = int(days_to_ref_date / pd.Timedelta(1, "d"))

    timeframe = 365 + days_to_ref_date
except:
    js.alert("Did you enter a date value? Refresh and try again.")

module_columns = {
    "m1": [
        "Person ID",
        "Surname",
        "Forename",
        "Dob (ccyy-mm-dd)",
        "Gender",
        "Ethnicity",
        "Postcode",
        "UPN - Unique Pupil Number",
        "ULN - Young Persons Unique Learner Number",
        "UPN and ULN unavailable reason",
    ],
    "m2": [
        "Person ID",
        "Requests Record ID",
        "Date Request Was Received",
        "Initial Request Whilst In RYA",
        "Request Outcome Date",
        "Request Outcome",
        "Request Mediation",
        "Request Tribunal",
        "Exported - Child Or Young Person Moves Out Of LA Before Assessment Is Completed",
        "New start date",
    ],
    "m3": [
        "Person ID",
        "Requests Record ID",
        "Assessment Outcome To Issue EHCP",
        "Assessment Outcome Date",
        "Assessment Mediation",
        "Assessment Tribunal",
        "Other Mediation",
        "Other Tribunal",
        "Twenty Weeks Time Limit Exceptions Apply",
    ],
    "m4": [
        "Person ID",
        "Request Records ID",
        "EHC Plan Start Date",
        "Residential Settings",
        "Worked based learning activity",
        "Personal budget taken up",
        "Personal budget - organised arrangements",
        "Personal budget - direct payments",
        "Date EHC Plan Ceased",
        "Reason EHC Plan Ceased",
    ],
    "m5": [
        "Person ID",
        "Request Records ID",
        "EHC Plan (Transfer)",
        "Residential Settings",
        "Worked based learning activity",
        "EHCP review decisions date",
    ],
}


# Utilities
def age_buckets(age):
    if age < 1:
        return "Under 1"
    elif age <= 4:
        return "1-4 years"
    elif age <= 9:
        return "5-9 years"
    elif age <= 15:
        return "10-15 years"
    else:
        return "16 & over"


def timeliness_buckets(time_delta):
    if time_delta <= pd.Timedelta(45, "d"):
        return "45 days or less"
    elif time_delta <= pd.Timedelta(90, "d"):
        return "46-90 days"
    elif time_delta <= pd.Timedelta(150, "d"):
        return "91-150 days"
    elif time_delta <= pd.Timedelta(365, "d"):
        return "151-365 days"
    elif time_delta <= pd.Timedelta(720, "d"):
        return "1-2 years"
    elif time_delta <= pd.Timedelta(1085, "d"):
        return "2-3 years"
    elif time_delta <= pd.Timedelta(1450, "d"):
        return "3-4 years"
    else:
        return "over 4 years"


def add_identifiers(identifiers, m2, m3, m4, m5):
    identifiers["Gender"] = identifiers["Gender"].map(
        {1: "Male", 2: "Female", 0: "Not Stated", 9: "Neither"}
    )
    identifiers["Age"] = pd.to_datetime("today") - pd.to_datetime(
        identifiers["Dob (ccyy-mm-dd)"], format="%d/%m/%Y", errors="coerce"
    )
    identifiers["Age"] = round((identifiers["Age"] / np.timedelta64(1, "Y")))
    identifiers["Age Group"] = identifiers["Age"].apply(age_buckets)

    m2 = pd.merge(m2, identifiers, on="Person ID", how="left")
    m3 = pd.merge(m3, identifiers, on="Person ID", how="left")
    m4 = pd.merge(m4, identifiers, on="Person ID", how="left")
    m5 = pd.merge(m5, identifiers, on="Person ID", how="left")
    return m2, m3, m4, m5


def html_plot(plot, width, tall=False):
    # Used to centralise arguments for making html plots
    if tall == True:
        plot = plot.to_html(
            include_plotlyjs=False,
            full_html=False,
            default_height="600px",
            default_width="1295px",
        )
    elif width == "n":
        plot = plot.to_html(
            include_plotlyjs=False,
            full_html=False,
            default_height="400px",
            default_width="640px",
        )
    elif width == "w":
        plot = plot.to_html(
            include_plotlyjs=False,
            full_html=False,
            default_height="400px",
            default_width="1295px",
        )
    return plot


# Plotting functions
def hist_for_categories(df):
    hist_gender = px.histogram(df, x="Gender").update_layout(
        title_x=0.5, yaxis_title="Number of children"
    )
    hist_ethnicity = px.histogram(df, x="Ethnicity").update_layout(
        title_x=0.5, yaxis_title="Number of children"
    )
    hist_age = px.histogram(df, x="Age Group", color="Gender").update_layout(
        title_x=0.5, yaxis_title="Number of children"
    )

    return hist_gender, hist_ethnicity, hist_age


def box_for_categories(df, y):
    box_gender = px.box(df, x="Gender", y=y).update_layout(title_x=0.5)
    box_ethnicity = px.box(df, x="Ethnicity", y=y).update_layout(title_x=0.5)
    box_age = px.box(df, x="Age Group", y=y, color="Gender").update_layout(title_x=0.5)

    return box_gender, box_ethnicity, box_age


# Calculation functions
def entire_cohort(df):
    gender, ethnicity, age = hist_for_categories(df)

    gender.update_layout(title="Entire cohort by gender")
    ethnicity.update_layout(title="Entire cohort ethnicity")
    age.update_layout(title="Entire cohort age and gender")

    count = len(df["Person ID"].unique())

    fig_count = go.Figure(go.Indicator(value=count))
    fig_count.update_layout(
        title={
            "text": "Total children in SEN2 data",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    gender = html_plot(gender, "n")
    ethnicity = html_plot(ethnicity, "w")
    age = html_plot(age, "n")
    fig_count = html_plot(fig_count, "n")

    return gender, ethnicity, age, fig_count


def ehc_ceased_year(df):
    """
    df = module 4
    """
    df = df[df["Date EHC Plan Ceased"].notna()]
    df["Date EHC Plan Ceased"] = pd.to_datetime(
        df["Date EHC Plan Ceased"], dayfirst=True
    )  # format="%d/%m/%Y", errors="corece")
    df["Time Since EHC Ceased"] = np.datetime64("today") - df["Date EHC Plan Ceased"]
    ehc_ceased_in_year = df[df["Time Since EHC Ceased"] <= pd.Timedelta(timeframe, "d")]
    count_ehc_ceased = len(ehc_ceased_in_year)
    reason_ech_ceased = (
        ehc_ceased_in_year.groupby("Reason EHC Plan Ceased")["Reason EHC Plan Ceased"]
        .count()
        .reset_index(name="count")
    )

    fig_count_ceased = go.Figure(go.Indicator(value=count_ehc_ceased))
    fig_count_ceased.update_layout(
        title={
            "text": "EHC ceased in the last year",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )
    gender_hist, ethnicity_hist, age_hist = hist_for_categories(ehc_ceased_in_year)

    gender_hist.update_layout(title="EHC ceased this year by gender")
    ethnicity_hist.update_layout(title="EHC ceased this year by ethnicity")
    age_hist.update_layout(title="EHC ceased this year by age and gender")

    reason_ceased_pie = px.pie(
        reason_ech_ceased,
        values="count",
        names="Reason EHC Plan Ceased",
        title="Reason EHC ceased",
    ).update_layout(title_x=0.5)

    fig_count_ceased = html_plot(fig_count_ceased, "n")
    gender_hist = html_plot(gender_hist, "n")
    ethnicity_hist = html_plot(ethnicity_hist, "w")
    age_hist = html_plot(age_hist, "n")
    reason_ceased_pie = html_plot(reason_ceased_pie, "n")

    return fig_count_ceased, gender_hist, ethnicity_hist, age_hist, reason_ceased_pie


def ehc_starting_year(df):
    """
    df = module 4
    """
    df = df[df["EHC Plan Start Date"].notna()]
    df["EHC Plan Start Date"] = pd.to_datetime(
        df["EHC Plan Start Date"], format="%d/%m/%Y", errors="coerce"
    )
    df["Time since EHC Started"] = np.datetime64("today") - df["EHC Plan Start Date"]
    ehc_started_in_year = df[
        df["Time since EHC Started"] <= pd.Timedelta(timeframe, "d")
    ]
    count_ehc_started = len(ehc_started_in_year)
    fig_count_started = go.Figure(go.Indicator(value=count_ehc_started))
    fig_count_started.update_layout(
        title={
            "text": "EHC started in the last year",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    gender_hist, ethnicity_hist, age_hist = hist_for_categories(ehc_started_in_year)

    gender_hist.update_layout(title="EHC started this year by gender")
    ethnicity_hist.update_layout(title="EHC started this year by ethnicity")
    age_hist.update_layout(title="EHC started this year by age and gender")

    fig_count_started = html_plot(fig_count_started, "n")
    gender_hist = html_plot(gender_hist, "n")
    ethnicity_hist = html_plot(ethnicity_hist, "w")
    age_hist = html_plot(age_hist, "n")

    return fig_count_started, gender_hist, ethnicity_hist, age_hist


def ass_completed_year(df):
    """
    df = module 3
    """
    df_completed = df[df["Assessment Outcome Date"].notna()]
    df_completed["Time Since Ass Completion"] = np.datetime64("today") - pd.to_datetime(
        df_completed["Assessment Outcome Date"], format="%d/%m/%Y", errors="coerce"
    )
    ass_this_year = df_completed[
        df_completed["Time Since Ass Completion"] <= pd.Timedelta(timeframe, "d")
    ]

    ass_year_outcomes = (
        ass_this_year.groupby("Assessment Outcome To Issue EHCP")[
            "Assessment Outcome To Issue EHCP"
        ]
        .count()
        .reset_index(name="count")
    )
    ass_outcomes_pie = px.pie(
        ass_year_outcomes,
        values="count",
        names="Assessment Outcome To Issue EHCP",
        title="Outcomes of assessments closed this year",
    ).update_layout(title_x=0.5)

    assessments_completed_this_year = len(ass_this_year)
    fig_count_completed = go.Figure(go.Indicator(value=assessments_completed_this_year))
    fig_count_completed.update_layout(
        title={
            "text": "Assessments completed in the last year",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    gender_hist, ethnicity_hist, age_hist = hist_for_categories(ass_this_year)

    gender_hist.update_layout(title="Assessments completed this year by gender")
    ethnicity_hist.update_layout(title="Assessments completed this year by ethnicity")
    age_hist.update_layout(title="Assessments completed this year by age and gender")

    fig_count_completed = html_plot(fig_count_completed, "n")
    gender_hist = html_plot(gender_hist, "n")
    ethnicity_hist = html_plot(ethnicity_hist, "w")
    age_hist = html_plot(age_hist, "n")
    ass_outcomes_pie = html_plot(ass_outcomes_pie, "n")

    return fig_count_completed, gender_hist, ethnicity_hist, age_hist, ass_outcomes_pie


def closed_ass_timeframes(df1, df2):
    """
    Time between request being recieved in module 2, and now, (filtering closed assessments from module 3).

    df1 = module 2
    df2 = module 3
    """

    df = pd.merge(
        df1,
        df2,
        on=[
            "Person ID",
            "Requests Record ID",
            "Gender",
            "Ethnicity",
            "Age",
            "Age Group",
        ],
        how="inner",
    )

    df["Date Request Was Received"] = pd.to_datetime(
        df["Date Request Was Received"], format="%d/%m/%Y", errors="coerce"
    )
    df["Assessment Outcome Date"] = pd.to_datetime(
        df["Assessment Outcome Date"], format="%d/%m/%Y", errors="coerce"
    )
    df = df[
        (df["Assessment Outcome Date"].notna())
        & (
            (pd.to_datetime("today") - df["Assessment Outcome Date"])
            <= pd.Timedelta(timeframe, "d")
        )
    ]

    df["closed_ass_timeliness"] = (
        df["Assessment Outcome Date"] - df["Date Request Was Received"]
    ) / pd.Timedelta(1, "day")
    df["closed_ass_timeliness"] = df["closed_ass_timeliness"].round()

    gender_box, ethnicity_box, age_box = box_for_categories(df, "closed_ass_timeliness")
    gender_box.update_layout(
        title="Closed assessment timeliness distribution by gender",
        yaxis_title="Timeliness (days)",
    )
    ethnicity_box.update_layout(
        title="Closed assessment timeliness distribution by ethnicity",
        yaxis_title="Timeliness (days)",
    )
    age_box.update_layout(
        title="Closed assessment timeliness distribution by age",
        yaxis_title="Timeliness (days)",
    )

    gender_box = html_plot(gender_box, "n")
    ethnicity_box = html_plot(ethnicity_box, "w")
    age_box = html_plot(age_box, "n")

    return gender_box, ethnicity_box, age_box


def open_ass_timeframes(df1, df2):
    """
    Time between request being recieved in module 2, and now, (filtering closed assessments from module 3).

    df1 = module 2
    df2 = module 3
    """
    df = pd.merge(
        df1,
        df2,
        on=[
            "Person ID",
            "Requests Record ID",
            "Gender",
            "Ethnicity",
            "Age",
            "Age Group",
        ],
        how="inner",
    )
    df = df[df["Date Request Was Received"].notna()]

    uncompleted_assessment_requests = len(df[df["Assessment Outcome Date"].isna()])
    uncompleted_requests = go.Figure(
        go.Indicator(value=uncompleted_assessment_requests)
    )
    uncompleted_requests.update_layout(
        title={
            "text": "Uncompleted assessment requests",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    df = df[df["Assessment Outcome Date"].isna()]
    df["Date Request Was Received"] = pd.to_datetime(
        df["Date Request Was Received"], format="%d/%m/%Y", errors="coerce"
    )
    df["open_ass_timeliness"] = (
        np.datetime64("today") - df["Date Request Was Received"]
    ) / pd.Timedelta(1, "day")
    df["open_ass_timeliness"] = df["open_ass_timeliness"].round()

    gender_box, ethnicity_box, age_box = box_for_categories(df, "open_ass_timeliness")
    gender_box.update_layout(
        title="Open assessment timeliness distribution by gender",
        yaxis_title="Timeliness (days)",
    )
    ethnicity_box.update_layout(
        title="Open assessment timeliness distribution by ethnicity",
        yaxis_title="Timeliness (days)",
    )
    age_box.update_layout(
        title="Open assessment timeliness distribution by age",
        yaxis_title="Timeliness (days)",
    )

    uncompleted_requests = html_plot(uncompleted_requests, "n")
    gender_box = html_plot(gender_box, "n")
    ethnicity_box = html_plot(ethnicity_box, "w")
    age_box = html_plot(age_box, "n")

    return uncompleted_requests, gender_box, ethnicity_box, age_box


def requests_fn(df):
    df = df[df["Date Request Was Received"].notna()]
    df["Date Request Was Received"] = pd.to_datetime(
        df["Date Request Was Received"], format="%d/%m/%Y", errors="coerce"
    )
    df["Request Outcome Date"] = pd.to_datetime(
        df["Request Outcome Date"], format="%d/%m/%y", errors="coerce"
    )

    req_timeliness_df = df[df["Request Outcome Date"].notna()]
    req_timeliness_df["Request Delta"] = (
        req_timeliness_df["Request Outcome Date"]
        - req_timeliness_df["Date Request Was Received"]
    ) / pd.Timedelta(1, "days")
    req_timeliness_df["Request Delta"] = req_timeliness_df["Request Delta"].round()

    df["Request Timeframe"] = np.datetime64("today") - df["Date Request Was Received"]
    requests_this_year = df[df["Request Timeframe"] <= pd.Timedelta(timeframe, "d")]

    count_requests_this_year = len(requests_this_year)
    fig_count_req = go.Figure(go.Indicator(value=count_requests_this_year))
    fig_count_req.update_layout(
        title={
            "text": "Requests this year",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    request_outcomes = (
        df.groupby("Request Outcome")["Request Outcome"]
        .count()
        .reset_index(name="count")
    )
    requests_pie = px.pie(
        request_outcomes, values="count", names="Request Outcome"
    ).update_layout(title_x=0.5)

    gender_hist, ethnicity_hist, age_hist = hist_for_categories(df)
    gender_hist.update_layout(
        title="Distribution of gender for requests this year",
        yaxis_title="Timeliness (days)",
    )
    ethnicity_hist.update_layout(
        title="Distribution of ethnicity for requests this year",
        yaxis_title="Timeliness (days)",
    )
    age_hist.update_layout(
        title="Distribution of age for requests this year",
        yaxis_title="Timeliness (days)",
    )

    fig_count_req = html_plot(fig_count_req, "n")
    gender_hist = html_plot(gender_hist, "n")
    ethnicity_hist = html_plot(ethnicity_hist, "w")
    age_hist = html_plot(age_hist, "n")
    requests_pie = html_plot(requests_pie, "n")

    return fig_count_req, gender_hist, ethnicity_hist, age_hist, requests_pie


def multiple_appearances(m2, m3):
    m2 = m2.groupby("Person ID")["Person ID"].count().reset_index(name="count")
    m2 = m2[m2["count"] > 1]
    multiple_m2 = go.Figure(go.Indicator(value=len(m2)))
    multiple_m2.update_layout(
        title={
            "text": "Children appearing in the requests list multiple times",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    m3 = m3.groupby("Person ID")["Person ID"].count().reset_index(name="count")
    m3 = m3[m3["count"] > 1]
    multiple_m3 = go.Figure(go.Indicator(value=len(m2)))
    multiple_m3.update_layout(
        title={
            "text": "Children appearing in the assessments list multiple times",
            "y": 0.6,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    multiple_m2 = html_plot(multiple_m2, "n")
    multiple_m3 = html_plot(multiple_m3, "n")

    return multiple_m2, multiple_m3


def journeys(m2, m3):
    m2 = m2[m2["Date Request Was Received"].notna()]
    m2["Request"] = "Request Made"

    m3["Assessment Complete"] = m3["Assessment Outcome Date"].apply(
        lambda x: (
            "Assessment Completed" if pd.notna(x) else "Assessment not yet completed"
        )
    )

    df = pd.merge(
        m2,
        m3[
            [
                "Requests Record ID",
                "Person ID",
                "Assessment Outcome To Issue EHCP",
                "Assessment Complete",
            ]
        ],
        on=["Person ID", "Requests Record ID"],
        how="left",
    )

    df["Assessment Complete"] = df["Assessment Complete"].fillna(
        "Assessment uncompleted"
    )
    df["Assessment Outcome To Issue EHCP"] = df[
        "Assessment Outcome To Issue EHCP"
    ].fillna("No assessment outcome")

    fig = px.parallel_categories(
        df,
        dimensions=[
            "Request",
            "Request Outcome",
            "Assessment Complete",
            "Assessment Outcome To Issue EHCP",
        ],
    )
    fig.update_layout(margin=dict(l=50, r=50, t=50, b=50))

    fig = html_plot(fig, "w")

    return fig


def plan_length_plots(m4):
    m4["EHC Plan Start Date"] = pd.to_datetime(
        m4["EHC Plan Start Date"], format="%d/%m/%Y"
    )
    m4["Date EHC Plan Ceased"] = pd.to_datetime(
        m4["Date EHC Plan Ceased"], format="%d/%m/%Y"
    )

    df_open = m4[m4["Date EHC Plan Ceased"].isna() & m4["EHC Plan Start Date"].notna()]
    df_open["Plan length"] = pd.to_datetime("today") - df_open["EHC Plan Start Date"]
    df_open["Plan length"] = df_open["Plan length"].apply(timeliness_buckets)
    open_gender_hist = px.histogram(
        df_open,
        x="Plan length",
        color="Gender",
        title="Currently open plan lengths by gender",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )
    open_ethnicity_hist = px.histogram(
        df_open,
        x="Plan length",
        color="Ethnicity",
        title="Currently open plan lengths by ethnicity",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )
    open_age_hist = px.histogram(
        df_open,
        x="Plan length",
        color="Age Group",
        title="Currently open plan lengths by age",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )

    df_closed = m4[
        m4["Date EHC Plan Ceased"].notna() & m4["EHC Plan Start Date"].notna()
    ]
    df_closed["Plan length"] = (
        df_closed["Date EHC Plan Ceased"] - df_closed["EHC Plan Start Date"]
    )
    df_closed["Plan length"] = df_closed["Plan length"].apply(timeliness_buckets)
    closed_gender_hist = px.histogram(
        df_closed,
        x="Plan length",
        color="Gender",
        title="Closed plan lengths by gender",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )
    closed_ethnicity_hist = px.histogram(
        df_closed,
        x="Plan length",
        color="Ethnicity",
        title="Closed plan lengths by ethnicity",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )
    closed_age_hist = px.histogram(
        df_closed,
        x="Plan length",
        color="Age Group",
        title="Closed plan lengths by age",
        category_orders={
            "Plan length": [
                "45 days or less",
                "46-90 days",
                "91-150 days",
                "151-365 days",
                "1-2 years",
                "2-3 years",
                "3-4 years",
                "over 4 years",
            ]
        },
    )

    open_gender_hist = html_plot(open_gender_hist, "n")
    open_ethnicity_hist = html_plot(open_ethnicity_hist, "w", tall=True)
    open_age_hist = html_plot(open_age_hist, "n")
    closed_gender_hist = html_plot(closed_gender_hist, "n")
    closed_ethnicity_hist = html_plot(closed_ethnicity_hist, "w", tall=True)
    closed_age_hist = html_plot(closed_age_hist, "n")

    return (
        open_gender_hist,
        open_ethnicity_hist,
        open_age_hist,
        closed_gender_hist,
        closed_ethnicity_hist,
        closed_age_hist,
    )

####################################
# XML INGRESS
####################################
def get_values(xml_elements, table_dict: dict, xml_block):
    # st.write(table_dict)
    # st.write(xml_block)
    for element in xml_elements:
        try:
            table_dict[element] = xml_block.find(element).text
        except:
            table_dict[element] = pd.NA
    return table_dict 

class XMLtoCSV():
    header = pd.DataFrame(
        columns = [
            'Collection',
            'Year',
            'Reference Date'
        ]
    )

    persons = pd.DataFrame(
        columns = [
            'FamilyName',
            'Firstname',
            'PersonBirthDate',
            'Sex',
            'Ethnicity',
            'PostCode',
            'UPN',
            'UniqueLearnerNumber',
            'UPNunknown',
        ]
    )

    requests = pd.DataFrame(
        columns = [
            "ReceivedDate",
            "RYA",
            "RequestOutcomeDate",
            "RequestOutcome",
            "RequestMediation",
            "RequestTribunal",
            "Exported",
        ]
    )

    assessments = pd.DataFrame(
        columns=[
            "AssessmentOutcome",
            "AssessmentOutcomeDate",
            "AssessmentMediation",
            "AssessmentTribunal",
            "OtherMediation",
            "OtherTribunal",
            "Week20",
        ]
    )

    named_plan = pd.DataFrame(
        columns = [
            'StartDate',
            'URN',
            'UKPRN',
            'SENSetting', 
            'PlacementRank',
            'SENunitIndicator',
            'ResourcedProvisionIndicator',
            'PlanRes',
            'PlanWPB',
            'PB',
            'OA',
            'DP',
            'CeaseDate',
            'CeaseReason'
        ]
    )

    active_plans = pd.DataFrame(
        columns = [
            'TransferLA',
            'URN',
            'UKPRN',
            'SENSetting',
            'SENSettingOther',
            'PlacementRank',
            'EntryDate',
            'LeavingDate',
            'SENunitIndicator',
            'ResourcedProvisionIndicator',
            'RES',
            'WPB',
            'SENtype',
            'SENtypeRank',
            'ReviewMeeting',
            'ReviewOutcome',
            'LastReview'
        ]
    )

    

    def __init__(self, root):
        self.child_id = 0
        header = root.find('Header')
        self.Header = self.create_header(header)
        self.name = None

        children  = root.find('Persons')

        for child in children.findall('Person'):      
            self.create_child(child)

        self.named_plan = self.named_plan[self.named_plan['StartDate'].notna()].copy()

 

    def create_header(self, header):

        header_dict = {}
        collection_details = header.find('CollectionDetails')
        collection_elements = ['Collection', 'Year', 'ReferenceDate'] 
        header_dict = get_values(collection_elements, header_dict, collection_details)

        source = header.find("Source")
        source_elements = [
            "SourceLevel",
            "LEA",
            "SoftwareCode",
            "Release",
            "SerialNo",
            "DateTime",
        ]
        header_dict = get_values(source_elements, header_dict, source)

        header_df = pd.DataFrame.from_dict([header_dict])
        return header_df    
    
    def create_child(self, person):
        self.create_person(person)
        self.create_requests(person)


    def create_person(self, child):
        forename = child.find('Forename').text
        surname = child.find('Surname').text
        self.name = f'{forename} {surname}'
        self.child_id += 1
        person_dict = {}
        elements = self.persons.columns
        person_dict = get_values(elements, person_dict, child)
        person_dict['child_id'] = self.child_id

        persons_df = pd.DataFrame.from_dict([person_dict])
        self.persons = pd.concat(
            [self.persons, persons_df], ignore_index=True
        )

    def create_requests(self, child):
        self.requests_id = 0
        elements = self.requests.columns
        requests_list = []
        
        requests = child.findall('Requests')
        for request in requests:
            requests_dict = {}
            self.requests_id += 1

            requests_dict = get_values(elements, requests_dict, request)

            requests_dict['child_id'] = self.child_id
            requests_dict['requests_id'] = self.requests_id

            requests_list.append(requests_dict)

            self.create_assessments(request)
            self.create_active_plans(request)

        requests_df = pd.DataFrame(requests_list)
        self.requests = pd.concat(
            [self.requests, requests_df], ignore_index=True
        )

        
    
    def create_assessments(self, request):
        assessment_list = []
        elements = self.assessments.columns
        self.assessment_id = 0

        assessments = request.findall('Assessment')

        for assessment in assessments:

            # assessments
            self.assessment_id += 1
            assessment_dict = {}

            assessment_dict = get_values(elements, assessment_dict, assessment)
            
            assessment_dict['name'] = self.name
            assessment_dict['child_id'] = self.child_id
            assessment_dict['requests_id'] = self.requests_id
            assessment_dict['assessment_id'] = self.assessment_id
            
            assessment_list.append(assessment_dict)

            # named_plans
            self.create_named_plan(assessment)

        
        assessment_df = pd.DataFrame(assessment_list)
        self.assessments = pd.concat(
            [self.assessments, assessment_df], ignore_index=True
        )

    def create_named_plan(self, assessment):

        named_plan_elements= [
            'StartDate',
            'PlanRes',
            'PlanWPB',
            'PB',
            'OA',
            'DP',
            'CeaseDate',
            'CeaseReason'
            ]
        named_plan_dict = {}

        plan_detail_elements = [
            'URN',
            'UKPRN',
            'SENSetting',
            'SENSettingOther',
            'PlacementRank',
            'SENunitIndicator',
            'ResourcedProvisionIndicator'
        ]

        named_plan_locs = assessment.find('NamedPlan')
        plan_detail_list = []
        
        if named_plan_locs:
            for plan_detail in named_plan_locs.findall('PlanDetail'):
                named_plan_dict = get_values(named_plan_elements, named_plan_dict, named_plan_locs)
                
                named_plan_dict = get_values(plan_detail_elements, named_plan_dict, plan_detail)
                named_plan_dict['name'] = self.name
                named_plan_dict['child_id'] = self.child_id
                named_plan_dict['requests_id'] = self.requests_id
                named_plan_dict['assessment_id'] = self.assessment_id

                plan_detail_list.append(named_plan_dict)

            named_plan_df = pd.DataFrame(plan_detail_list)
            self.named_plan = pd.concat(
                [self.named_plan, named_plan_df], ignore_index=True
            )

    def create_active_plans(self, request):
        active_plans_list = []
        
        active_plan_elements = [
            'TransferLA',
            'RES',
            'WPB',
            'ReviewMeeting',
            'ReviewOutcome',
            'LastReview'
        ]
        placement_detail_elements = [
            'URN',
            'SENSetting',
            'SENSettingOther',
            'PlacementRank',
            'EntryDate',
            'LeavingDate',
            'SENunitIndicator',
            'ResourcedProvisionIndicator',
        ]
        sen_need_elements = [
            'SENtype',
            'SENtypeRank'
        ]

        active_plan_locs = request.find('ActivePlans')
        if active_plan_locs:
            placement_detail_locs = active_plan_locs.findall('PlacementDetail')
            sen_need_locs = active_plan_locs.find('SENneed')
            
            for placement_detail in placement_detail_locs:  
                active_plans_dict = {} 
                active_plans_dict = get_values(active_plan_elements, active_plans_dict, active_plan_locs)
                active_plans_dict = get_values(placement_detail_elements, active_plans_dict, placement_detail)
                active_plans_dict = get_values(sen_need_elements, active_plans_dict, sen_need_locs)
                active_plans_dict['name'] = self.name
                active_plans_dict['child_id'] = self.child_id
                active_plans_dict['requests_id'] = self.requests_id

                active_plans_list.append(active_plans_dict)

            active_plan_df = pd.DataFrame(active_plans_list)
            self.active_plans = pd.concat(
                [self.active_plans, active_plan_df], ignore_index=True
            )

def convert_for_sen2_tool(m1, m2, m3, m4, m5):
    m1.rename(columns={'child_id': 'Person ID',
                        'PersonBirthDate': 'Dob (ccyy-mm-dd)',
                        'Sex':'Gender'},
                          inplace=True)
    
    m2.rename(columns={'requests_id':'Requests Record ID',
                       'RequestOutcome':'Request Outcome',
                       'RequestOutcomeDate':'Request Outcome Date',
                       'ReceivedDate':'Date Request Was Received'},
              inplace=True)
    
    m3.rename(columns={'requests_id':'Requests Record ID',
                       'AssessmentOutcome':'Assessment Outcome To Issue EHCP',
                       'AssessmentOutcomeDate':'Assessment Outcome Date'},
              inplace=True)
    
    m4.rename(columns={'requests_id':'Requests Record ID',
                       'StartDate':'EHC Plan Start Date',
                       'CeaseDate':'Date EHC Plan Ceased',
                       'CeaseReason':'Reason EHC Plan Ceased',},
              inplace=True)
    
    output_dict = {'m1':m1,
                   'm2':m2,
                   'm3':m3,
                   'm4':m4,
                   'm5':m5}
    
    js.console.log(output_dict)
    
    return output_dict
                    


def convert_data(root: ET.Element):
    datafiles = XMLtoCSV(root)

    return datafiles



##############
# Main App
##############

input_type = js.window.input_type.to_py()
modules = {}

js.console.log(f'Input type detected: {input_type}')

if input_type == 'csv':
    for key, df in dfs.items():
        for module_name, column_list in module_columns.items():
            if list(df.columns) == column_list:
                modules[module_name] = df
elif input_type == 'xml':   
    data_files = convert_data(root)
    modules = convert_for_sen2_tool(data_files.persons,
                                data_files.requests,
                                data_files.assessments,
                                data_files.named_plan,
                                data_files.active_plans)
else:
    js.alert("Did you upload the correct files, more info in the instructions.")


if len(modules.keys()) != 5:
    js.alert(f"Modules found {modules.keys()}, please check column names.")

modules["m2"], modules["m3"], modules["m4"], modules["m5"] = add_identifiers(
    modules["m1"], modules["m2"], modules["m3"], modules["m4"], modules["m5"]
)


# Plot outputs
(
    js.document.total_gender_hist,
    js.document.total_ethnicity_hist,
    js.document.total_age_hist,
    js.document.total_count_indicator,
) = entire_cohort(modules["m1"])

(
    js.document.ehc_ceased_indicator,
    js.document.ehc_ceased_gender_hist,
    js.document.ehc_ceased_ethnicity_hist,
    js.document.ehc_ceased_age_hist,
    js.document.ehc_ceased_reason_pie,
) = ehc_ceased_year(modules["m4"])

(
    js.document.ehc_started_indicator,
    js.document.ehc_started_gender_hist,
    js.document.ehc_started_ethnicity_hist,
    js.document.ehc_started_age_hist,
) = ehc_starting_year(modules["m4"])

(
    js.document.ass_completed_indicator,
    js.document.ass_completed_gender_hist,
    js.document.ass_completed_ethnicity_hist,
    js.document.ass_completed_age_hist,
    js.document.ass_completed_reason_pie,
) = ass_completed_year(modules["m3"])

(
    js.document.ass_open_timeframe_indicator,
    js.document.ass_open_timeframe_gender_box,
    js.document.ass_open_timeframe_ethnicity_box,
    js.document.ass_open_timeframe_age_box,
) = open_ass_timeframes(modules["m2"], modules["m3"])


(
    js.document.ass_closed_timeframe_gender_box,
    js.document.ass_closed_timeframe_ethnicity_box,
    js.document.ass_closed_timeframe_age_box,
) = closed_ass_timeframes(modules["m2"], modules["m3"])

(
    js.document.req_count_indicator,
    js.document.req_gender_box,
    js.document.req_ethnicity_box,
    js.document.req_age_box,
    req_pie,
) = requests_fn(modules["m2"])

js.document.multiple_m2, js.document.multiple_m3 = multiple_appearances(
    modules["m2"], modules["m3"]
)

js.document.journeys = journeys(modules["m2"], modules["m3"])

(
    js.document.open_plan_length_gender_hist,
    js.document.open_plan_length_ethnicity_hist,
    js.document.open_plan_length_age_hist,
    js.document.closed_plan_length_gender_hist,
    js.document.closed_plan_length_ethnicity_hist,
    js.document.closed_plan_length_age_hist,
) = plan_length_plots(modules["m4"])
