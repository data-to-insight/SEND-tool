import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

import urllib
import urllib3
import json
import requests


"""
conversion rates from place to place
volummes of things happening by category by period eg closure reason by year
treat like an updateable written report
EHCPs issued this year
Assessments completed this year (plus outcome breakdown)
Assessments open now (plus assessment duration)
Requests (plus request outcome)

age
gender
ethnic background
by location

by age/gender compared to population
by ethnicity compared to population
by location if possible
by duration since plan started
And then similar sets for:

 
click through drilldowns would be cool
Same chart appearing next to each chart per cohort (so structure by stage or by cohort)
"""

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


def ehc_ceased_year(df):
    # currentyly 2 years for dummy data
    df = df[df["Date EHC Plan Ceased"].notna()]
    df["Date EHC Plan Ceased"] = pd.to_datetime(
        df["Date EHC Plan Ceased"], dayfirst=True
    )  # format="%d/%m/%Y", errors="corece")
    df["Time Since EHC Ceased"] = np.datetime64("today") - df["Date EHC Plan Ceased"]
    ehc_ceased_in_year = df[df["Time Since EHC Ceased"] <= pd.Timedelta(730, "d")]
    st.write(ehc_ceased_in_year)


uploaded_files = st.file_uploader("pls", accept_multiple_files=True)


if uploaded_files:

    dfs = {
        uploaded_file.name: pd.read_csv(uploaded_file)
        for uploaded_file in uploaded_files
    }

    modules = {}
    for key, df in dfs.items():
        for module_name, column_list in module_columns.items():
            if list(df.columns) == column_list:
                modules[module_name] = df

    # st.write(loaded_files.keys())

    # Assessments pie chart
    ass_outcomes = (
        modules["m3"]
        .groupby(["Assessment Outcome To Issue EHCP"])[
            "Assessment Outcome To Issue EHCP"
        ]
        .count()
        .reset_index(name="count")
    )
    assessment_outcome_plot = px.pie(
        ass_outcomes, values="count", names="Assessment Outcome To Issue EHCP"
    )
    st.plotly_chart(assessment_outcome_plot)

    # Request to outcome timeliness
    requests = modules["m2"][modules["m2"].notna()]

    requests["Request Timeliness"] = pd.to_datetime(
        requests["Request Outcome Date"], format="%d/%m/%Y"
    ) - pd.to_datetime(requests["Date Request Was Received"], format="%d/%m/%Y")

    requests["Request Timeliness"] = (
        (requests["Request Timeliness"] / np.timedelta64(1, "D"))
        .round()
        .astype("int", errors="ignore")
    )

    request_timeliness_plot = px.histogram(requests, x="Request Timeliness")
    st.plotly_chart(request_timeliness_plot)

    postcode_count = (
        modules["m1"].groupby("Postcode")["Postcode"].count().reset_index(name="count")
    )

    ehc_ceased_year(modules["m4"])
