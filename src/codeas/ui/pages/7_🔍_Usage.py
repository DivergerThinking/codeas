import json
from pathlib import Path

import pandas as pd
import streamlit as st


def read_usage_data():
    log_file = Path(".codeas/agent_executions.json")
    if log_file.exists():
        with open(log_file, "r") as f:
            return json.load(f)
    return []


def count_n_requests(usage_data):
    return len(usage_data)


def count_n_conversations(usage_data):
    return len(set(item["conversation_id"] for item in usage_data))


def calculate_total_cost(usage_data):
    return sum(item["cost"]["total_cost"] for item in usage_data)


def calculate_cost_by_days(usage_data):
    cost_by_days = {}
    for item in usage_data:
        date = item["timestamp"].split("T")[0]
        cost_by_days[date] = cost_by_days.get(date, 0) + item["cost"]["total_cost"]
    return cost_by_days


def calculate_usage_by_days(usage_data):
    usage_by_days = {}
    for item in usage_data:
        date = item["timestamp"].split("T")[0]
        if date not in usage_by_days:
            usage_by_days[date] = {"Cost": 0, "Requests": 0, "Conversations": set()}
        usage_by_days[date]["Cost"] += item["cost"]["total_cost"]
        usage_by_days[date]["Requests"] += 1
        usage_by_days[date]["Conversations"].add(item["conversation_id"])

    # Convert sets to counts
    for date in usage_by_days:
        usage_by_days[date]["Conversations"] = len(usage_by_days[date]["Conversations"])

    return usage_by_days


def calculate_usage_by_model(usage_data):
    usage_by_model = {}
    for item in usage_data:
        model = item["model"]  # Correct access to the model
        if model not in usage_by_model:
            usage_by_model[model] = {"Requests": 0, "Cost": 0}
        usage_by_model[model]["Requests"] += 1
        usage_by_model[model]["Cost"] += item["cost"]["total_cost"]
    return usage_by_model


def display_usage_metrics(usage_data):
    col1, col2 = st.columns(2)

    with col1:
        st.metric("🔢 Total requests", count_n_requests(usage_data))
        st.metric("💬 Total conversations", count_n_conversations(usage_data))

    with col2:
        total_cost = calculate_total_cost(usage_data)
        st.metric("💰 Total cost", f"${total_cost:.2f}")


def prepare_usage_by_day_df(usage_data):
    usage_by_days = calculate_usage_by_days(usage_data)
    df = pd.DataFrame.from_dict(usage_by_days, orient="index").reset_index()
    df.columns = ["Date", "Cost", "Requests", "Conversations"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    df["Cumulative Cost"] = df["Cost"].cumsum()
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    return df


def display_usage_by_day(df):
    st.dataframe(
        df.set_index("Date").style.format(
            {
                "Cost": "${:.2f}",
                "Cumulative Cost": "${:.2f}",
                "Requests": "{:,d}",
                "Conversations": "{:,d}",
            }
        )
    )


def prepare_usage_by_model_df(usage_data):
    usage_by_model = calculate_usage_by_model(usage_data)
    model_df = pd.DataFrame.from_dict(usage_by_model, orient="index").reset_index()
    model_df.columns = ["Model", "Requests", "Cost"]
    model_df = model_df.sort_values("Cost", ascending=False)
    total_cost = model_df["Cost"].sum()
    model_df["Percentage"] = model_df["Cost"] / total_cost * 100
    return model_df


def display_usage_by_model(model_df):
    st.dataframe(
        model_df.set_index("Model").style.format(
            {"Cost": "${:.2f}", "Requests": "{:,d}", "Percentage": "{:.2f}%"}
        )
    )


def display_chat_usage():
    usage_data = read_usage_data()

    display_usage_metrics(usage_data)

    st.subheader("📅 Usage by day")
    usage_by_day_df = prepare_usage_by_day_df(usage_data)
    display_usage_by_day(usage_by_day_df)

    st.subheader("🤖 Usage by model")
    usage_by_model_df = prepare_usage_by_model_df(usage_data)
    display_usage_by_model(usage_by_model_df)


def usage_page():
    st.subheader("🔍 Usage Statistics")
    with st.expander("Chat usage", icon="💬", expanded=True):
        display_chat_usage()


usage_page()
