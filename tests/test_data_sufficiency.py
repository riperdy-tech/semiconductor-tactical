from pathlib import Path

from tactical_engine.data.sufficiency import ComponentValidationStatus, check_data_sufficiency


def test_data_sufficiency_evaluation():
    report = check_data_sufficiency(
        data_dir=Path("data/processed"),
        universe=["MU", "SNDK", "SKHY", "USD", "SMH", "SPY"],
    )

    assert report.equity_rth == ComponentValidationStatus.VALIDATED
    assert report.extended_hours == ComponentValidationStatus.UNVALIDATED
    assert report.covered_calls == ComponentValidationStatus.UNVALIDATED
    assert report.margin_financing == ComponentValidationStatus.VALIDATED
    assert not report.is_full_replication_supported
    assert "UNVALIDATED" in report.details["covered_calls"]
    assert "UNVALIDATED" in report.details["extended_hours"]
