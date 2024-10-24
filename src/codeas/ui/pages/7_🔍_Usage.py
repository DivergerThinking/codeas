import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.core.usage_tracker import usage_tracker


def read_usage_data(file_path: str):
    log_file = Path(file_path)
    if log_file.exists():
        with open(log_file, "r") as f:
            return json.load(f)
    return {}


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


def calculate_usage_by_generator(usage_data):
    usage_by_generator = {}
    for item in usage_data:
        generator = item["generator"]
        if generator not in usage_by_generator:
            usage_by_generator[generator] = {"Requests": 0, "Cost": 0}
        usage_by_generator[generator]["Requests"] += 1
        usage_by_generator[generator]["Cost"] += item["cost"]["total_cost"]
    return usage_by_generator


def display_usage_metrics(usage_data):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💬 Total conversations", count_n_conversations(usage_data))
    with col2:
        st.metric("🔢 Total requests", count_n_requests(usage_data))
    with col3:
        total_cost = calculate_total_cost(usage_data)
        st.metric("💰 Total cost", f"${total_cost:.2f}")


def display_generator_metrics(usage_data):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔢 Total requests", count_n_requests(usage_data))
    with col2:
        total_cost = calculate_total_cost(usage_data)
        st.metric("💰 Total cost", f"${total_cost:.2f}")


def display_generator_by_generator(usage_data):
    usage_by_generator = calculate_usage_by_generator(usage_data)
    df = pd.DataFrame.from_dict(usage_by_generator, orient="index").reset_index()
    df.columns = ["Generator", "Requests", "Cost"]
    df = df.sort_values("Requests", ascending=False)
    total_requests = df["Requests"].sum()
    df["Percentage"] = df["Requests"] / total_requests * 100
    st.dataframe(
        df.set_index("Generator").style.format(
            {"Cost": "${:.2f}", "Requests": "{:,d}", "Percentage": "{:.2f}%"}
        )
    )


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
    model_df = model_df.sort_values("Requests", ascending=False)
    total_requests = model_df["Requests"].sum()
    model_df["Percentage"] = model_df["Requests"] / total_requests * 100
    return model_df


def display_usage_by_model(model_df):
    st.dataframe(
        model_df.set_index("Model").style.format(
            {"Cost": "${:.2f}", "Requests": "{:,d}", "Percentage": "{:.2f}%"}
        )
    )


def display_chat_usage():
    usage_data = usage_tracker.load_data().get("chat", [])

    display_usage_metrics(usage_data)
    if any(usage_data):
        st.subheader("📅 Usage by day")
        usage_by_day_df = prepare_usage_by_day_df(usage_data)
        display_usage_by_day(usage_by_day_df)
    if any(usage_data):
        st.subheader("🤖 Usage by model")
        usage_by_model_df = prepare_usage_by_model_df(usage_data)
        display_usage_by_model(usage_by_model_df)


def display_prompt_generator_usage():
    usage_data = usage_tracker.load_data().get("generator", [])
    display_generator_metrics(usage_data)
    if any(usage_data):
        st.subheader("🤖 Usage by generator")
        display_generator_by_generator(usage_data)


def display_use_cases_usage():
    usage_data = usage_tracker.load_data()
    display_documentation_usage(usage_data)
    display_deployment_usage(usage_data)
    display_testing_usage(usage_data)
    display_refactoring_usage(usage_data)


def display_documentation_usage(usage_data):
    st.subheader("📚 Documentation")
    docs_data = usage_data.get("generate_docs", {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔢 Total requests", docs_data.get("count", 0))
    with col2:
        st.metric("💰 Total cost", f"${docs_data.get('total_cost', 0):.2f}")

    with st.expander("Sections"):
        sections = [
            "project_overview",
            "setup_and_development",
            "architecture",
            "ui",
            "db",
            "api",
            "testing",
            "deployment",
            "security",
        ]

        sections_data = []
        for section in sections:
            section_data = usage_data.get(f"generate_{section}", {})
            sections_data.append(
                {
                    "Section": section.replace("_", " ").title(),
                    "Requests": section_data.get("count", 0),
                    "Cost": section_data.get("total_cost", 0),
                }
            )

        df = pd.DataFrame(sections_data)
        st.dataframe(
            df.set_index("Section").style.format(
                {"Requests": "{:,d}", "Cost": "${:.2f}"}
            ),
        )


def display_deployment_usage(usage_data):
    st.subheader("🚀 Deployment")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Defining deployment strategy**:")
        define_data = usage_data.get("define_deployment", {})
        st.metric("🔢 Total requests", define_data.get("count", 0))
        st.metric("💰 Total cost", f"${define_data.get('total_cost', 0):.2f}")
    with col2:
        st.write("**Generating deployment**:")
        generate_data = usage_data.get("generate_deployment", {})
        st.metric("🔢 Total requests", generate_data.get("count", 0))
        st.metric("💰 Total cost", f"${generate_data.get('total_cost', 0):.2f}")


def display_testing_usage(usage_data):
    st.subheader("🧪 Testing")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Defining testing strategy**:")
        strategy_data = usage_data.get("define_testing_strategy", {})
        st.metric("🔢 Total requests", strategy_data.get("count", 0))
        st.metric("💰 Total cost", f"${strategy_data.get('total_cost', 0):.2f}")
    with col2:
        st.write("**Generating tests from strategy**:")
        tests_data = usage_data.get("generate_tests_from_strategy", {})
        st.metric("🔢 Total requests", tests_data.get("count", 0))
        st.metric("💰 Total cost", f"${tests_data.get('total_cost', 0):.2f}")


def display_refactoring_usage(usage_data):
    st.subheader("🔄 Refactoring")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Defining refactoring files**:")
        define_data = usage_data.get("define_refactoring_files", {})
        st.metric("🔢 Total requests", define_data.get("count", 0))
        st.metric("💰 Total cost", f"${define_data.get('total_cost', 0):.2f}")
    with col2:
        st.write("**Generating proposed changes**:")
        propose_data = usage_data.get("generate_proposed_changes", {})
        st.metric("🔢 Total requests", propose_data.get("count", 0))
        st.metric("💰 Total cost", f"${propose_data.get('total_cost', 0):.2f}")
    with col3:
        st.write("**Generating diffs**:")
        diffs_data = usage_data.get("generate_diffs", {})
        st.metric("🔢 Total requests", diffs_data.get("count", 0))
        st.metric("💰 Total cost", f"${diffs_data.get('total_cost', 0):.2f}")


def usage_page():
    st.subheader("🔍 Usage")
    with st.expander("Chat", icon="💬", expanded=True):
        display_chat_usage()
    with st.expander("Prompt generator", icon="📝", expanded=True):
        display_prompt_generator_usage()
    with st.expander("Use cases", icon="🤖", expanded=True):
        display_use_cases_usage()


usage_page()
