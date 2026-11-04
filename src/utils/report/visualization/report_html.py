"""Assemble a finished report: the HTML the PDF is made from, and a portable .md.

Same functions as the SME repo, so the notebook's save cell is unchanged. The
corp report contains no Mermaid diagrams or charts, so ``embed_diagrams`` has
nothing to embed and returns the text as it is.
"""

from src.utils.report.visualization.report_style import REPORT_CSS, tag_wide_tables


MARKDOWN_EXTENSIONS = ("tables", "fenced_code", "footnotes")
MARKDOWN_EXTENSION_CONFIGS = {"footnotes": {"USE_DEFINITION_ORDER": False}}


def build_report_html(markdown_text: str) -> str:
    """The complete HTML document the PDF is rendered from."""

    import markdown as markdown_lib

    body = markdown_lib.markdown(
        markdown_text or "",
        extensions=list(MARKDOWN_EXTENSIONS),
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )
    return (
        '<html><head><meta charset="utf-8"><style>'
        + REPORT_CSS
        + "</style></head><body>"
        + tag_wide_tables(body)
        + "</body></html>"
    )


def embed_diagrams(markdown_text: str) -> str:
    """No diagrams in the corp report: the Markdown is already portable."""

    return markdown_text or ""
