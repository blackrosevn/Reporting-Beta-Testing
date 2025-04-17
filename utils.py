import streamlit as st

def get_navigation_options():
    """Return navigation options based on user role."""
    if st.session_state.user_role == "admin":
        return [
            "Dashboard",
            "Report Templates",
            "Assign Reports",
            "Report Status",
            "Organizations",
            "Users"
        ]
    elif st.session_state.user_role == "department":
        return [
            "Dashboard",
            "Assign Reports",
            "Report Status",
            "My Reports"
        ]
    elif st.session_state.user_role == "unit":
        return [
            "Dashboard",
            "My Reports",
            "Submit Report"
        ]
    else:
        return ["Dashboard"]
