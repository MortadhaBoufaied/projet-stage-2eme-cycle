"""End-to-end tests for the Streamlit UI using AppTest.

Covers: page rendering, sidebar navigation, login page, all page modules,
display components, and field mapping components.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

# Project root: one level up from the tests/ directory.
_ROOT = Path(__file__).resolve().parents[1]

# All page render() functions share the same four-argument signature:
# render(registry, recommender, profiles, company).
# MagicMock auto-creates any attribute accessed, so pages that call
# registry.load_latest() or profiles.load() won't crash.
_MOCK_IMPORTS = (
    "from unittest.mock import MagicMock\n"
    "_MOCK_ARGS = [MagicMock(), MagicMock(), MagicMock(), 'test-company']\n"
)


def _page_app(module_path: str) -> AppTest:
    """Create an AppTest from a temp script that imports and calls render().

    AppTest.from_function() requires inspect.getsource(), which fails for
    dynamically generated functions.  AppTest.from_file() needs a real file
    on disk.  This helper writes a minimal wrapper script to a temp file
    and returns the AppTest instance ready to .run().
    """
    script = (
        f"{_MOCK_IMPORTS}"
        f"import importlib\n"
        f"mod = importlib.import_module('{module_path}')\n"
        f"mod.render(*_MOCK_ARGS)\n"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8",
    )
    tmp.write(script)
    tmp.flush()
    tmp.close()
    return AppTest.from_file(tmp.name)


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

class TestDashboardPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.dashboard"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_page_header(self):
        at = _page_app("src.ui.pages.dashboard"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Dashboard" in t for t in texts)


# ---------------------------------------------------------------------------
# Credit page
# ---------------------------------------------------------------------------

class TestCreditPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.credit"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_page_header(self):
        at = _page_app("src.ui.pages.credit"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Credit risk" in t for t in texts)


# ---------------------------------------------------------------------------
# Demand page
# ---------------------------------------------------------------------------

class TestDemandPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.demand"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_page_header(self):
        at = _page_app("src.ui.pages.demand"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Demand" in t for t in texts)


# ---------------------------------------------------------------------------
# Training page
# ---------------------------------------------------------------------------

class TestTrainingPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.training"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_model_family_radio(self):
        at = _page_app("src.ui.pages.training"))
        at.run(timeout=30)
        radios = at.radio
        assert len(radios) >= 1, "Expected at least one radio button"
        assert "Credit risk" in radios[0].options
        assert "Demand" in radios[0].options

    def test_default_selection_is_credit_risk(self):
        at = _page_app("src.ui.pages.training"))
        at.run(timeout=30)
        radios = at.radio
        assert radios[0].value == "Credit risk"


# ---------------------------------------------------------------------------
# Policies page
# ---------------------------------------------------------------------------

class TestPoliciesPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.policies"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_page_header(self):
        at = _page_app("src.ui.pages.policies"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Company rules" in t for t in texts)

    def test_has_save_button(self):
        """Verify the policies page contains a save/apply button."""
        at = _page_app("src.ui.pages.policies"))
        at.run(timeout=30)
        button_labels = [b.label for b in at.button]
        assert len(button_labels) >= 1, "Expected at least one button"


# ---------------------------------------------------------------------------
# History page
# ---------------------------------------------------------------------------

class TestHistoryPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.history"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_page_header(self):
        at = _page_app("src.ui.pages.history"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Model versions" in t for t in texts)


# ---------------------------------------------------------------------------
# Help page
# ---------------------------------------------------------------------------

class TestHelpPage:
    def test_renders_without_error(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        assert not at.exception, f"Page raised: {at.exception}"

    def test_shows_pipeline_table(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("decision pipeline" in t.lower() for t in texts)

    def test_shows_mission_section(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Mission" in t for t in texts)

    def test_shows_credit_workflow(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Credit risk workflow" in t for t in texts)

    def test_shows_demand_workflow(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Demand workflow" in t for t in texts)

    def test_shows_governance_section(self):
        at = _page_app("src.ui.pages.help"))
        at.run(timeout=30)
        texts = [m.value for m in at.markdown]
        assert any("Governance" in t for t in texts)


# ---------------------------------------------------------------------------
# Display components
# ---------------------------------------------------------------------------

class TestDisplayComponents:
    def test_metric_cards_renders(self):
        """Verify metric_cards renders st.metric widgets."""

        def page():
            from src.ui.components.display import metric_cards
            metric_cards({"a": 1, "b": 2.5}, ["a", "b"])

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.metric) == 2

    def test_status_banner_renders(self):
        """Verify status_banner renders markdown with the correct CSS class."""

        def page():
            from src.ui.components.display import status_banner
            status_banner("success", "All good")

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        texts = [m.value for m in at.markdown]
        assert any("status-success" in t for t in texts)
        assert any("All good" in t for t in texts)

    def test_download_button_renders(self):
        """Verify download_button renders a download_button widget."""

        def page():
            import pandas as pd
            from src.ui.components.display import download_button
            df = pd.DataFrame({"x": [1, 2]})
            download_button(df, "test.csv")

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.download_button) == 1


# ---------------------------------------------------------------------------
# Field components
# ---------------------------------------------------------------------------

class TestFieldComponents:
    def test_csv_uploader_renders(self):
        """Verify csv_uploader renders a file_uploader widget."""

        def page():
            from src.ui.components.fields import csv_uploader
            csv_uploader("Upload CSV", "test_upload")

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.file_uploader) == 1

    def test_model_select_renders(self):
        """Verify model_select renders a selectbox widget."""

        def page():
            from src.ui.components.fields import model_select
            model_select(["a", "b", "c"], key="test_model")

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.selectbox) == 1
        assert at.selectbox[0].options == ["a", "b", "c"]

    def test_slider_pair_renders(self):
        """Verify slider_pair renders two slider widgets."""

        def page():
            from src.ui.components.fields import slider_pair
            slider_pair("Low", "High", 0.5, 0.7)

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.slider) == 2

    def test_checkbox_group_renders(self):
        """Verify checkbox_group renders checkbox widgets."""

        def page():
            from src.ui.components.fields import checkbox_group
            checkbox_group(["opt1", "opt2", "opt3"], key_prefix="test_cg")

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        assert len(at.checkbox) == 3


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------

class TestLoginPage:
    def test_renders_without_error(self):
        """Verify the login page renders without raising an exception."""

        def page():
            from src.ui.login import render_login
            render_login()

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception

    def test_login_form_has_username_and_password(self):
        """Verify the login form has username and password inputs."""

        def page():
            from src.ui.login import render_login
            render_login()

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        text_inputs = at.text_input
        assert len(text_inputs) >= 2, f"Expected >= 2 text inputs, got {len(text_inputs)}"

    def test_signup_toggle_button_exists(self):
        """Verify the 'Create an account' button exists."""

        def page():
            from src.ui.login import render_login
            render_login()

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        button_labels = [b.label for b in at.button]
        assert any("Create an account" in label for label in button_labels)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

class TestSidebar:
    def test_sidebar_renders_with_navigation(self):
        """Verify sidebar renders with grouped navigation items."""

        def page():
            from src.ui.components.sidebar import render_sidebar
            render_sidebar()

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        buttons = at.button
        button_labels = [b.label for b in buttons]
        # Should have 7 nav items + 1 sign out button
        assert any("Dashboard" in label for label in button_labels)
        assert any("Credit" in label for label in button_labels)
        assert any("Sign out" in label for label in button_labels)

    def test_sidebar_shows_brand(self):
        """Verify sidebar shows the FDS brand."""

        def page():
            from src.ui.components.sidebar import render_sidebar
            render_sidebar()

        at = AppTest.from_function(page)
        at.run(timeout=15)
        assert not at.exception
        texts = [m.value for m in at.markdown]
        assert any("FDS" in t for t in texts)


# ---------------------------------------------------------------------------
# Page registry completeness
# ---------------------------------------------------------------------------

class TestPageRegistry:
    def test_all_pages_in_registry(self):
        """Verify PAGE_MAP contains all expected pages."""
        from src.ui.pages import PAGE_MAP
        expected = {"dashboard", "credit", "demand", "training", "policies", "history", "help"}
        assert set(PAGE_MAP.keys()) == expected

    def test_all_pages_have_titles(self):
        """Verify PAGE_TITLES has entries for all pages."""
        from src.ui.pages import PAGE_TITLES
        from src.ui.pages import PAGE_MAP
        for key in PAGE_MAP:
            assert key in PAGE_TITLES, f"Missing title for page: {key}"

    def test_all_pages_renderable(self):
        """Verify each page module has a callable render function."""
        from src.ui.pages import PAGE_MAP
        for key, module in PAGE_MAP.items():
            assert hasattr(module, "render"), f"Page module '{key}' missing render()"
            assert callable(module.render), f"Page module '{key}' render is not callable"
