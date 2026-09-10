from __future__ import annotations

import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the company policies page."""

    st.markdown(
        '<div class="page-header"><h1>Company rules</h1>'
        '<p class="lead">Personalize recommendations without changing model predictions.</p></div>',
        unsafe_allow_html=True,
    )

    profile = profiles.load(company)

    with st.form("company_policy"):
        st.markdown("### Workspace identity")
        left, right = st.columns(2)
        display = left.text_input(
            "Company display name",
            profile.display_name,
            placeholder="Example: North Region Finance",
        )
        currency = right.text_input("Currency", profile.currency)
        language = left.selectbox(
            "Preferred language",
            ["English", "French", "Arabic"],
            index=["English", "French", "Arabic"].index(profile.language)
            if profile.language in ["English", "French", "Arabic"]
            else 0,
        )
        human = right.checkbox("Require human approval", profile.require_human_approval)

        st.markdown("### Recommendation controls")
        rules = st.text_area(
            "Mandatory rules",
            "\n".join(profile.recommendation_rules),
            height=115,
            placeholder="One rule per line",
        )
        blocked = st.text_area(
            "Forbidden action keywords",
            "\n".join(profile.forbidden_actions),
            height=115,
            placeholder="One phrase per line",
        )
        submitted = st.form_submit_button("Save company rules", type="primary")

    if submitted:
        profile.display_name = display.strip()
        profile.currency = currency.strip() or "TND"
        profile.language = language
        profile.require_human_approval = human
        profile.recommendation_rules = [x.strip() for x in rules.splitlines() if x.strip()]
        profile.forbidden_actions = [x.strip() for x in blocked.splitlines() if x.strip()]
        profiles.save(profile)
        st.success("Company rules saved.")
