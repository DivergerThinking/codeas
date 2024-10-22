import streamlit as st


def home_page():
    st.subheader("🏠 Codeas")
    st.markdown(
        """
    Codeas is a tool that helps you **boost your software development processes using generative AI**.
    """
    )
    st.markdown(
        """
    The following use cases are currently implemented:
    """
    )
    st.page_link("pages/1_💬_Chat.py", label="Chat", icon="💬")
    st.page_link("pages/2_📚_Documentation.py", label="Documentation", icon="📚")
    st.page_link("pages/3_🚀_Deployment.py", label="Deployment", icon="🚀")
    st.page_link("pages/4_🧪_Testing.py", label="Testing", icon="🧪")
    st.page_link("pages/5_🔄_Refactoring.py", label="Refactoring", icon="🔄")
    st.page_link("pages/6_📝_Prompts.py", label="Prompts", icon="📝")
    st.page_link("pages/7_🔍_Usage.py", label="Usage", icon="🔍")
    st.markdown(
        """
    For more information about the tool, visit the [GitHub repository](https://github.com/DivergerThinking/codeas).
    """
    )


if __name__ == "__main__":
    home_page()
