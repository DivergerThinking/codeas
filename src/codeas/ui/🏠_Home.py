import streamlit as st


def home_page():
    st.title("Codeas")
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
    st.page_link("pages/1_📚_Documentation.py", label="Documentation", icon="📚")
    st.page_link("pages/2_🚀_Deployment.py", label="Deployment", icon="🚀")
    st.page_link("pages/3_🧪_Testing.py", label="Testing", icon="🧪")
    st.page_link("pages/4_🔄_Refactoring.py", label="Refactoring", icon="🔄")
    st.markdown(
        """
    For more information about the tool, visit the [GitHub repository](https://github.com/DivergerThinking/codeas).
    """
    )


if __name__ == "__main__":
    home_page()
