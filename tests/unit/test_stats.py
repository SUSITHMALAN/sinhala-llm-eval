import pytest

from lankallm.stats import (
    cohens_kappa,
    holm_correction,
    mcnemar_exact,
    two_proportion_z,
    wilson_interval,
)


def test_wilson_matches_textbook_value() -> None:
    low, high = wilson_interval(8, 10)
    assert low == pytest.approx(0.4902, abs=1e-3)
    assert high == pytest.approx(0.9433, abs=1e-3)


def test_wilson_with_no_data_is_uninformative() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_mcnemar_exact_known_value() -> None:
    assert mcnemar_exact(1, 5) == pytest.approx(0.21875)
    assert mcnemar_exact(0, 0) == 1.0


def test_two_proportion_z_equal_groups() -> None:
    z, p = two_proportion_z(10, 20, 10, 20)
    assert z == 0.0
    assert p == pytest.approx(1.0)


def test_kappa_known_value() -> None:
    a = ["y"] * 25 + ["n"] * 25
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    assert cohens_kappa(a, b) == pytest.approx(0.4)


def test_kappa_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        cohens_kappa(["y"], ["y", "n"])


def test_holm_correction() -> None:
    assert holm_correction([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
