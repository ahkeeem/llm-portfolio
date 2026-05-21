"""
Prompt Registry — loads and renders Jinja2 templates from the prompts/ directory.

Usage:
    from core.prompts import render_prompt

    prompt = render_prompt("rag_policy", question="What is...", context="...")
"""
import os
from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

_PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../prompts"))

_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=False,
)


@lru_cache(maxsize=64)
def _get_template(name: str):
    """Load a template by name (without the .j2 extension)."""
    try:
        return _env.get_template(f"{name}.j2")
    except TemplateNotFound:
        raise FileNotFoundError(
            f"Prompt template '{name}.j2' not found in {_PROMPTS_DIR}. "
            f"Available: {list_templates()}"
        )


def render_prompt(template_name: str, **kwargs) -> str:
    """
    Render a Jinja2 prompt template with the given variables.

    Args:
        template_name: Name of the template (without .j2 extension).
                       e.g. "rag_policy", "classify_email", "eval_faithfulness"
        **kwargs: Template variables to substitute.

    Returns:
        The rendered prompt string.
    """
    tpl = _get_template(template_name)
    return tpl.render(**kwargs)


def list_templates() -> list[str]:
    """Return all available prompt template names."""
    return [
        t.replace(".j2", "")
        for t in _env.list_templates()
        if t.endswith(".j2")
    ]
