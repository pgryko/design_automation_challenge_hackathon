"""Custom template tags for style rendering."""

import re

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def extract_colors(style_summary: str) -> list[dict[str, str]]:
    """Extract color hex codes and their descriptions from style summary."""
    if not style_summary:
        return []

    colors = []
    # Match patterns like #1a417f (description) or #1a417f
    pattern = r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\s*(?:\(([^)]+)\))?"
    matches = re.findall(pattern, style_summary)

    seen = set()
    for hex_code, description in matches:
        hex_full = f"#{hex_code}"
        if hex_full.lower() not in seen:
            seen.add(hex_full.lower())
            colors.append({"hex": hex_full, "description": description or ""})

    return colors[:12]  # Limit to 12 colors


@register.simple_tag
def render_color_swatches(style_summary: str) -> str:
    """Render color swatches from style summary."""
    colors = extract_colors(style_summary)
    if not colors:
        return ""

    swatches_html = ['<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">']
    for color in colors:
        tooltip = f'{color["hex"]} - {color["description"]}' if color["description"] else color["hex"]
        swatches_html.append(
            f'<div style="position: relative;" title="{tooltip}">'
            f'<div style="width: 2rem; height: 2rem; border-radius: 0.5rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); border: 1px solid #e5e7eb; cursor: pointer; background-color: {color["hex"]};"></div>'
            f"</div>"
        )
    swatches_html.append("</div>")
    return mark_safe("".join(swatches_html))


@register.filter
def format_style_section(style_summary: str, section: str) -> str:
    """Extract and format a specific section from style summary."""
    if not style_summary:
        return ""

    # Look for **Section**: content pattern
    pattern = rf"\*\*{section}\*\*:\s*(.+?)(?=\*\*|$)"
    match = re.search(pattern, style_summary, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""
