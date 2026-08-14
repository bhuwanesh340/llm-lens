"""Unit tests for project name normalization and slug derivation (T114).

Pure functions — no database required, so these run without Postgres.
"""

from __future__ import annotations

import pytest

from app.services.project_service import (
    InvalidProjectNameError,
    derive_slug,
    normalize_project_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("my-app", "my-app"),
        ("  my-app  ", "my-app"),
        ("My   Cool   App", "My Cool App"),
        ("\tTabbed\nName\t", "Tabbed Name"),
    ],
)
def test_normalize_trims_and_collapses_whitespace(raw: str, expected: str) -> None:
    assert normalize_project_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_normalize_rejects_empty_names(raw: str) -> None:
    with pytest.raises(InvalidProjectNameError):
        normalize_project_name(raw)


def test_normalize_rejects_over_length_names() -> None:
    with pytest.raises(InvalidProjectNameError):
        normalize_project_name("x" * 129)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("My Cool App", "my-cool-app"),
        ("MY COOL APP", "my-cool-app"),
        ("my_cool_app", "my-cool-app"),
        ("My  Cool   App", "my-cool-app"),
        ("checkout-service", "checkout-service"),
        ("Agent v2.1", "agent-v2-1"),
    ],
)
def test_derive_slug_is_case_and_separator_insensitive(name: str, expected: str) -> None:
    """FR-103: names differing only by case/whitespace resolve to one project."""

    assert derive_slug(name) == expected


def test_derive_slug_rejects_names_without_alphanumerics() -> None:
    with pytest.raises(InvalidProjectNameError):
        derive_slug("!!!")


def test_derive_slug_is_stable_across_equivalent_names() -> None:
    variants = ["Support Bot", "support bot", "  SUPPORT   BOT  ", "support-bot"]
    slugs = {derive_slug(normalize_project_name(v)) for v in variants}
    assert slugs == {"support-bot"}
