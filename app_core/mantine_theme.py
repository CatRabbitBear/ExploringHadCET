FONT_BODY = (
    "-apple-system, BlinkMacSystemFont, "
    "'Segoe UI', Roboto, Inter, system-ui, sans-serif"
)

FONT_HEADINGS = (
    "-apple-system, BlinkMacSystemFont, "
    "'Segoe UI', Roboto, Inter, system-ui, sans-serif"
)

THEME = {
    # Base typography
    "fontFamily": FONT_BODY,
    # Primary colour & shape
    "primaryColor": "brand",
    "defaultRadius": "sm",
    "black": "#2f4058",
    # Headings configuration
    "headings": {
        "fontFamily": FONT_HEADINGS,
        "fontWeight": 600,
        "color": "dark.9",
        "sizes": {
            "h1": {
                "fontSize": "2rem",  # ~32px
                "lineHeight": 1.25,
                "fontWeight": 700,
            },
            "h2": {
                "fontSize": "1.5rem",  # ~24px
                "lineHeight": 1.3,
                "fontWeight": 600,
            },
            "h3": {
                "fontSize": "1.25rem",  # ~20px
                "lineHeight": 1.35,
                "fontWeight": 600,
            },
            "h4": {
                "fontSize": "1.1rem",
                "lineHeight": 1.4,
                "fontWeight": 600,
            },
        },
    },
    # Optional: slightly calmer default text tone
    "colors": {
        "brand": [
            "#e3fafc",
            "#c5f6fa",
            "#99e9f2",
            "#66d9e8",
            "#3bc9db",
            "#22b8cf",
            "#15aabf",
            "#1098ad",
            "#0c8599",
            "#0b7285",
        ],
    },
    "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.08)",
        "md": "0 2px 6px rgba(0,0,0,0.10)",
    },
}
