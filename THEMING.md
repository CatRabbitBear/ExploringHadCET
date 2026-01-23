# Theming & Styling Guide

This app uses **multiple styling layers** because different parts of the stack are responsible for different things:

* **CSS** controls DOM layout and browser behaviour
* **Dash Mantine Components (DMC)** control UI components
* **Plotly** controls chart appearance

Mixing these concerns quickly leads to duplication and hard-to-maintain styling, so we keep them intentionally separated.

This document explains **where styling should live** and **how to decide where to make changes**.

---

## Styling Layers at a Glance

### 1. CSS (assets)

**Location**

```
assets/style.css
```

**Role**

* Layout and browser-level behaviour
* Things Plotly or Mantine don’t handle well

**Examples**

* Sticky headers
* Box shadows and borders
* Minor tweaks to how Plotly charts sit inside the page
* Global CSS variables (if needed)

**Rule of thumb**

> If it affects the DOM or scrolling/layout behaviour, it belongs in CSS.

---

### 2. Dash Mantine Components (UI layer)

**Location**

```
app_core/mantine_theme.py
```

**Role**

* Global look and feel of UI components
* Typography, radii, and base colours for Mantine components

**Examples**

* Font family
* Primary colour
* Default border radius

**Rule of thumb**

> If it styles buttons, cards, stacks, text, or layout components, it belongs in the Mantine theme or component props.

---

### 3. Plotly (chart layer)

**Location**

```
app_core/plotly_theme.py
```

**Role**

* Visual consistency across all charts
* Shared chart layout and interaction defaults

**Examples**

* Plotly templates
* Axis/grid styling
* Margins and hover behaviour
* Reusable layout helpers (2D/3D charts)

**Rule of thumb**

> If it changes how a chart looks or behaves, it belongs in the Plotly theme.

---

### 4. Colour tokens (shared)

**Location**

```
app_core/tokens_color.py
```

**Role**

* Single source of truth for colours used across the app

**Examples**

* Background and border colours
* Grid and legend colours
* Climate anomaly colour scales
* Categorical colours (e.g. winter buckets)

**Rule of thumb**

> If a colour is reused or has semantic meaning, define it here and import it where needed.

---

## Conventions

* Avoid hardcoded colours in page layouts or figure builders
  → use `tokens_color`
* Prefer shared Plotly layout helpers over per-figure styling
* Avoid inline CSS unless it solves a specific DOM problem
* New styling should follow these layers; existing code is migrated gradually

---

## Heading rules

* H1: page title (page.py only)
* H2: section titles (page.py)
* Markdown: start at H3, never use H1/H2
