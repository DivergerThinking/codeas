import os

import streamlit as st


def home_page():
    st.subheader("🏠 Codeas")

    # Add API key inputs
    st.sidebar.subheader("API Keys")
    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key", value=os.environ.get("OPENAI_API_KEY", ""), type="password"
    )
    anthropic_api_key = st.sidebar.text_input(
        "Anthropic API Key",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
    )
    google_api_key = st.sidebar.text_input(
        "Google API Key", value=os.environ.get("GOOGLE_API_KEY", ""), type="password"
    )
    azure_openai_api_key = st.sidebar.text_input(
        "Azure OpenAI API Key",
        value=os.environ.get("AZURE_OPENAI_API_KEY", ""),
        type="password",
    )
    azure_openai_endpoint = st.sidebar.text_input(
        "Azure OpenAI Endpoint",
        value=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        type="password",
    )

    # Set environment variables if API keys are provided
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    if anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    if azure_openai_api_key:
        os.environ["AZURE_OPENAI_API_KEY"] = azure_openai_api_key
    if azure_openai_endpoint:
        os.environ["AZURE_OPENAI_ENDPOINT"] = azure_openai_endpoint

    st.markdown(
        """
    Codeas is a tool that helps you **boost your software development processes using generative AI**.
    """
    )
    st.markdown(
        """
    For more information about the tool, visit the [GitHub repository](https://github.com/DivergerThinking/codeas).
    """
    )


if __name__ == "__main__":
    home_page()
