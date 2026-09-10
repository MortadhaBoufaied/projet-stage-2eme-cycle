from __future__ import annotations

import streamlit as st


def render(registry, recommender, profiles, company) -> None:
    """Render the company policies page."""

    st.markdown(
        '<div class="page-header"><h1>Company rules</h1>'
        '<p class="lead">Configure workspace settings and governance policies that control how '
        'recommendations are generated. These rules are applied on top of model predictions '
        'and do not affect the underlying model.</p></div>',
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
            help="Displayed in reports and exported CSVs. Does not affect model behavior.",
        )
        currency = right.text_input(
            "Currency",
            profile.currency,
            help="ISO currency code (e.g. TND, EUR, USD). Used in report headers and export formatting.",
        )
        language = left.selectbox(
            "Preferred language",
            ["English", "French", "Arabic"],
            index=["English", "French", "Arabic"].index(profile.language)
            if profile.language in ["English", "French", "Arabic"]
            else 0,
            help="Language for generated recommendation text and UI labels where localized.",
        )
        human = right.checkbox(
            "Require human approval",
            profile.require_human_approval,
            help="When enabled, every recommendation is flagged as 'pending review' until a human "
            "approves or overrides it. Recommended for production use.",
        )

        st.markdown("### Recommendation controls")
        st.markdown(
            "These rules are injected into the recommendation engine's prompt. "
            "Each rule is a constraint the engine must satisfy when generating actions."
        )
        rules = st.text_area(
            "Mandatory rules",
            "\n".join(profile.recommendation_rules),
            height=115,
            placeholder="One rule per line, e.g.:\nAlways request a credit report for amounts above 50000\nFlag any account older than 90 days",
            help="One rule per line. The recommendation engine will include these as hard constraints. "
            "Example: 'Always request a credit report for high-value applications'.",
        )
        blocked = st.text_area(
            "Forbidden action keywords",
            "\n".join(profile.forbidden_actions),
            height=115,
            placeholder="One phrase per line, e.g.:\nAuto-approve\nBypass review\nSkip validation",
            help="One phrase per line. Any recommendation containing these phrases is filtered out "
            "before it reaches the user. Use this to prevent risky automated actions.",
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
