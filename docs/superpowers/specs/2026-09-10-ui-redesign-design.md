# UI Redesign: Dark Minimal Theme + Icon Sidebar + Page Refactor

**Date:** 2026-09-10
**Branch:** feature/model-improvements
**Scope:** Full UI restyle, navigation overhaul, app.py refactor into per-page modules

---

## 1. Goal

Replace the current light-themed, gradient-heavy, sidebar-radio Streamlit UI with a dark minimal design (Vercel/Linear aesthetic), an always-expanded icon sidebar with Bootstrap Icons, a header with user menu, and a split-panel login page. Refactor the 543-line `app.py` monolith into separate page files.

**Measurable outcomes:**
- `app.py` reduced from ~543 lines to ~80 lines (routing + session gate only)
- Every page lives in its own file with a single `render()` function
- Zero emojis in navigation — all icons from Bootstrap Icons CDN
- Dark theme applied via CSS variables, no gradients, no shadows, no box-shadow

---

## 2. Theme: Dark Minimal

### 2.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#0a0a0a` | Page background |
| `--surface` | `#141414` | Cards, panels, form backgrounds |
| `--surface-2` | `#1c1c1c` | Hover states, elevated elements |
| `--border` | `#262626` | Dividers, card borders, input borders |
| `--text` | `#fafafa` | Primary text |
| `--text-muted` | `#737373` | Secondary text, captions, placeholders |
| `--accent` | `#3b82f6` | Buttons, links, active states, focus rings |
| `--accent-hover` | `#2563eb` | Button hover, link hover |
| `--success` | `#22c55e` | Success states, positive indicators |
| `--danger` | `#ef4444` | Error states, destructive actions |
| `--warning` | `#f59e0b` | Warning states, caution indicators |

### 2.2 Typography

- Font family: Inter (already in use via Google Fonts or local)
- No font-size changes from current defaults
- Primary text: `var(--text)`
- Muted text: `var(--text-muted)`

### 2.3 Styling Rules

- **Border-radius:** 8px everywhere (cards, inputs, buttons, tables)
- **Borders:** 1px solid `var(--border)` — no shadows, no box-shadow
- **Inputs:** `--surface` background, `--border` border, `--text` text, 8px radius, 40px height
- **Buttons:** `--accent` background, white text, 8px radius, 40px height. Hover: `--accent-hover`. Ghost variant: transparent bg, `--border` border, `--text` text
- **Cards:** `--surface` background, `--border` border, 8px radius, no shadow
- **Tables/DataFrames:** Dark rows, `--border` separators, `--surface` header
- **Expanders:** `--surface` background, `--border` border
- **Alerts:** Muted colored left border (4px) + `--surface` background. No bright background boxes
  - Error: `--danger` left border, `--danger` text
  - Success: `--success` left border, `--success` text
  - Warning: `--warning` left border, `--warning` text
  - Info: `--accent` left border, `--text` text
- **Metric cards:** `--surface` background, `--border` border, value in `--text`, label in `--text-muted`
- **Progress bars:** `--accent` fill, `--surface-2` track
- **File uploader:** Dashed `--border` border, `--surface` background, `--text-muted` text

### 2.4 Streamlit config

Update `.streamlit/config.toml`:
```toml
[theme]
base = "dark"
primaryColor = "#3b82f6"
backgroundColor = "#0a0a0a"
secondaryBackgroundColor = "#141414"
textColor = "#fafafa"
font = "sans serif"

[server]
headless = true
maxUploadSize = 200
```

---

## 3. Navigation: Always-Expanded Icon Sidebar

### 3.1 Layout

- Sidebar: always 240px wide, no collapse/expand
- Background: `--surface`
- Border-right: 1px solid `--border`
- Each nav item: Bootstrap Icon + label text, vertically stacked
- Active page: `--accent` left border (2px), `--surface-2` background tint
- Inactive pages: no background, `--text-muted` icon + text, hover → `--surface-2` bg + `--text`

### 3.2 Icons (Bootstrap Icons)

| Page | Icon class | Label |
|---|---|---|
| Dashboard | `bi-speedometer2` | Dashboard |
| Credit risk | `bi-graph-up-arrow` | Credit risk |
| Demand | `bi-graph-down-arrow` | Demand |
| Train models | `bi-tools` | Training |
| Policies | `bi-journal-text` | Policies |
| History | `bi-clock-history` | History |
| Help | `bi-question-circle` | Help |

### 3.3 Sidebar Bottom

- Thin divider line
- No user info or sign-out in sidebar (moved to header)

### 3.4 Header Bar

- Thin bar (48px height) across the top of the content area
- Left: current page title (white, 16px, semibold)
- Right: user avatar circle (first letter of username, accent background) + dropdown with sign-out option
- Background: `--bg` (same as page)
- Border-bottom: 1px solid `--border`

### 3.5 Implementation

- `src/ui/components/sidebar.py` — renders sidebar + header
- Uses `st.sidebar.markdown()` for sidebar content
- Uses `st.markdown()` at top of page for header bar
- Navigation via `st.sidebar.button()` with session state tracking (one button per page, active state tracked in `st.session_state["current_page"]`)
- Bootstrap Icons loaded via CDN in theme CSS:
  ```html
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  ```

---

## 4. Login Page

### 4.1 Layout

Split-panel design, vertically and horizontally centered:

- **Left panel** (40% width): `--surface` background, vertically centered content
  - Bootstrap Icon `bi-graph-up-arrow` (32px, accent color)
  - "Finance Decision Studio" (20px, semibold, white)
  - "Governed credit risk and demand analysis" (14px, `--text-muted`)
  - "Built for teams that need human oversight." (13px, `--text-muted`)
- **Right panel** (60% width): `--bg` background, centered form
  - "Welcome back" heading (18px, semibold, white)
  - Username input (full width)
  - Password input (full width)
  - Sign in button (full width, `--accent` background)
  - Error message below button (if any)

### 4.2 Form Behavior

- Same Streamlit form (`st.form`) as current
- Same `sign_in()` / `is_authenticated()` flow
- Error messages: `--danger` text, no background box
- Success: `st.rerun()` to main app

### 4.3 CSS

- Card/panel: no shadows, `--border` borders
- Inputs: dark bg, subtle border, light text
- Button: `--accent` bg, white text, hover `--accent-hover`

---

## 5. Page File Structure

### 5.1 Directory Layout

```
src/ui/
├── app.py              ← ~80 lines: config, theme, session gate, router
├── theme.py            ← dark minimal CSS
├── login.py            ← split login page
├── components/
│   ├── __init__.py     ← barrel exports
│   ├── sidebar.py      ← icon sidebar + header
│   ├── fields.py       ← CSV uploader, field mapping (keep existing)
│   └── display.py      ← metric cards, tables, charts (keep existing)
└── pages/
    ├── __init__.py     ← PAGES dict mapping keys → modules
    ├── dashboard.py    ← Dashboard
    ├── credit.py       ← Analyze credit risk
    ├── demand.py       ← Analyze demand
    ├── training.py     ← Train models (credit + forecast)
    ├── policies.py     ← Company policies
    ├── history.py      ← Model history
    └── help.py         ← Help
```

### 5.2 Page Contract

Every page module exports:

```python
def render(registry, recommender, profiles, company):
    """Render this page. Receives shared instances as arguments."""
    ...
```

- No global imports of `registry`, `recommender`, `profiles`, or `company`
- Each page is self-contained — can be understood and modified independently
- Pages use components from `src/ui/components/` for consistency

### 5.3 Router (`app.py`)

```python
st.set_page_config(page_title="Finance Decision Studio", page_icon="📈", layout="wide")
apply_dark_theme()

# Session gate
if not is_authenticated():
    render_login()
    st.stop()

# Sidebar + header
selected_page = render_sidebar()

# Clear stale results
clear_old_results()

# Shared instances
registry = ModelRegistry()
recommender = RecommendationEngine()
profiles = CompanyProfileStore()
company = "admin_company"
registry.company_dir(company, create=True)
profiles.save(profiles.load(company))

# Route to page
PAGES[selected_page].render(registry, recommender, profiles, company)
```

### 5.4 What Moves Where

| Current location | New location | Notes |
|---|---|---|
| Dashboard code (lines 161-181) | `pages/dashboard.py` | |
| Analyze credit risk (lines 184-214) | `pages/credit.py` | |
| Analyze demand (lines 218-248) | `pages/demand.py` | |
| Train models (lines 252-479) | `pages/training.py` | Largest page, ~230 lines |
| Company policies (lines 483-505) | `pages/policies.py` | |
| Model history (lines 509-522) | `pages/history.py` | |
| Help (lines 526-533) | `pages/help.py` | |
| Login hero + form (lines 62-112) | `login.py` | Split-panel redesign |
| Sidebar (lines 118-132) | `components/sidebar.py` | Icon sidebar redesign |
| CSS theme (theme.py) | `theme.py` | Dark minimal rewrite |
| Helper functions (lines 136-157) | `components/display.py` | `active()`, `load_csv()`, `cards()`, `data_summary()`, `mapping()`, `title()` become shared utilities imported by pages that need them |

---

## 6. Component Changes

### 6.1 Keep As-Is (just restyle via CSS)

- `components/fields.py` — `csv_uploader()`, `field_mapping()` — logic unchanged, CSS restyled via theme
- `components/display.py` — `metric_cards()`, `result_table()`, `result_chart()`, `download_button()` — logic unchanged, CSS restyled

### 6.2 New

- `components/sidebar.py` — icon sidebar + header bar (replaces sidebar code in app.py)

### 6.3 Remove

- `components/layout.py` — delete entirely. `page_header()`, `section_head()`, `rule_card()`, `empty_state()`, `status_message()` replaced by inline HTML/CSS in each page where needed (max 5-10 lines per usage, not worth a shared component)

---

## 7. What Stays the Same

- Streamlit as the framework
- `src/services/auth.py` — authentication logic unchanged
- `src/config.py` — env loading unchanged
- All backend services (training, models, registry, recommender, profiles)
- `src/ui/components/fields.py` — field mapping logic
- `src/ui/components/display.py` — result display logic
- `.env` file structure
- `artifacts/` directory structure

---

## 8. Migration Strategy

1. **Create new files first** — `login.py`, `pages/`, `components/sidebar.py`, new `theme.py`
2. **Update `app.py`** — replace monolith with router (~80 lines)
3. **Verify each page** — one at a time, ensure login → dashboard → each page works
4. **Delete old code** — remove unused functions from old `app.py`
5. **Test** — login flow, all 7 pages, sign-out, session expiry

---

## 9. Risks

- **Bootstrap Icons CDN dependency** — requires internet connection. Fallback: emoji icons if CDN unavailable
- **Streamlit sidebar limitations** — `st.sidebar` has fixed width behavior; the icon-only approach may need CSS overrides
- **Dark theme CSS conflicts** — Streamlit's built-in dark mode may conflict with custom CSS; test carefully
- **Training page complexity** — `pages/training.py` will still be ~230 lines due to hyperparameter forms; acceptable for now

---

## 10. Success Criteria

- [ ] Login works (form submits, credentials checked, session set)
- [ ] Sidebar shows icons + labels, active page highlighted
- [ ] Header shows page title + user menu
- [ ] All 7 pages render correctly with dark theme
- [ ] `app.py` is under 100 lines
- [ ] No emojis in navigation
- [ ] No gradients, no shadows, no box-shadow anywhere
- [ ] All existing functionality preserved (training, analysis, policies, history)
