"""Versioned prompt templates. Never edit a released version: add a new one."""

from __future__ import annotations

PROMPTS: dict[str, str] = {
    "p1": "{question}",
}


def render_prompt(version: str, question: str) -> str:
    try:
        template = PROMPTS[version]
    except KeyError as exc:
        raise ValueError(f"unknown prompt_version {version!r}") from exc
    return template.format(question=question)
