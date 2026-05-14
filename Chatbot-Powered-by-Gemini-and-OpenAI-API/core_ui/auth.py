import streamlit as st

ADMIN_EMAILS = {
    "yos225@lehigh.edu",
}

PARTICIPANT_EMAILS = {
    f"participant{i:02d}@lehigh.edu"
    for i in range(1, 21)
}

ASSIGNED_EMAILS = ADMIN_EMAILS | PARTICIPANT_EMAILS


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def assigned_email_valid(email: str) -> bool:
    email_norm = normalize_email(email)
    return email_norm in ASSIGNED_EMAILS


def render_signin_gate() -> bool:
    if st.session_state.get("email") and st.session_state.get("signed_in"):
        return True

    left, mid, right = st.columns([1.2, 2.2, 1.2])

    with mid:
        st.write("")
        st.write("")
        st.write("")
        st.markdown("## Welcome")
        st.caption("Enter the assigned study email to continue.")

        with st.form("signin_form", clear_on_submit=False):
            email_input = st.text_input(
                "Assigned study email",
                placeholder="participant01@lehigh.edu",
                key="lehigh_email",
            )

            submitted = st.form_submit_button("Continue")

            if submitted:
                email_norm = normalize_email(email_input)

                if not assigned_email_valid(email_norm):
                    st.error("Please use the assigned study email provided by the researcher.")

                    # Debug info: remove this later before deployment
                    st.caption(f"Debug entered: `{email_norm}`")
                    st.caption(f"Debug allowed examples: `{sorted(list(ASSIGNED_EMAILS))[:3]} ...`")
                    return False

                st.session_state["email"] = email_norm
                st.session_state["signed_in"] = True

                if email_norm in ADMIN_EMAILS:
                    st.session_state["rater_id"] = "admin_yos225"
                    st.session_state["is_admin"] = True
                else:
                    st.session_state["rater_id"] = email_norm.split("@")[0]
                    st.session_state["is_admin"] = False

                # clear study navigation state whenever signing in
                for k in [
                    "culture",
                    "ds_file",
                    "session_idx",
                    "current_session",
                    "selected_culture_lock",
                    "korean_model_type",
                ]:
                    st.session_state.pop(k, None)

                # clear cached sampled sessions
                for k in list(st.session_state.keys()):
                    if k.startswith("_sessions_cache") or k.startswith("_korean_sampled_sessions"):
                        st.session_state.pop(k, None)

                st.rerun()

    return False


def require_signed_in():
    if not st.session_state.get("email") or not st.session_state.get("signed_in"):
        st.error("You must sign in first. Please return to the home page.")
        st.stop()


def sign_out_to_home():
    keys_to_clear = [
        "email",
        "rater_id",
        "signed_in",
        "is_admin",
        "culture",
        "ds_file",
        "session_idx",
        "current_session",
        "selected_culture_lock",
        "korean_model_type",
        "lehigh_email",
    ]

    keys_to_clear += [
        k for k in list(st.session_state.keys())
        if k.startswith("_sessions_cache")
        or k.startswith("_korean_sampled_sessions")
    ]

    for k in keys_to_clear:
        st.session_state.pop(k, None)

    st.switch_page("Home.py")