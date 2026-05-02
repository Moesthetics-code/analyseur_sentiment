"""
Sentence-level sentiment heatmap.
Takes a list of sentence_analysis dicts and builds HTML
with background color intensity based on compound score.
"""
import re
import html


def _compound_to_rgba(compound: float, alpha: float = 0.35) -> str:
    """Maps compound score [-1, +1] to an RGBA color string."""
    if compound >= 0.05:
        # Green shades
        intensity = min(1.0, compound * 1.5)
        return f"rgba(52, 211, 153, {round(alpha * intensity, 2)})"
    elif compound <= -0.05:
        # Red shades
        intensity = min(1.0, abs(compound) * 1.5)
        return f"rgba(251, 113, 133, {round(alpha * intensity, 2)})"
    else:
        # Neutral blue
        return f"rgba(34, 211, 238, {round(alpha * 0.25, 2)})"


def _compound_to_border(compound: float) -> str:
    if compound >= 0.05:
        return "rgba(52, 211, 153, 0.5)"
    elif compound <= -0.05:
        return "rgba(251, 113, 133, 0.5)"
    return "rgba(34, 211, 238, 0.3)"


def build_highlight_html(sentence_analysis: list) -> str:
    """
    Returns an HTML string with each sentence wrapped in a styled span.
    """
    if not sentence_analysis:
        return ""

    parts = []
    for sa in sentence_analysis:
        text = html.escape(sa["sentence"])
        compound = sa.get("compound", 0)
        bg = _compound_to_rgba(compound)
        border = _compound_to_border(compound)
        score_label = f"{compound:+.2f}"

        tooltip = f"Score: {score_label}"
        span = (
            f'<span class="highlight-sentence" '
            f'style="background:{bg}; border-bottom: 2px solid {border}; '
            f'border-radius:3px; padding:1px 2px; cursor:default;" '
            f'data-compound="{compound}" '
            f'title="{tooltip}">'
            f'{text}'
            f'</span>'
        )
        parts.append(span)

    return " ".join(parts)