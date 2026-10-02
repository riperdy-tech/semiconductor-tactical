import argparse
import sys
from pathlib import Path

from tactical_engine.config import load_config
from tactical_engine.data.historical import CsvEquityDataProvider, HistoricalDataMissingError
from tactical_engine.data.validation import validate_symbol_bars


def run_data_doctor(
    data_dir: Path | str,
    symbols: list[str],
    expected_interval: str | None = None,
) -> bool:
    data_path = Path(data_dir)
    print("=" * 95)
    print(f"HISTORICAL DATA DOCTOR -- PATH: {data_path.resolve()}")
    if "sample_historical" in str(data_path):
        print(
            "DATA ORIGIN NOTICE: [SYNTHETIC FIXTURE DATA] "
            "Data is from sample_historical fixtures, NOT real market data."
        )
    if expected_interval:
        print(f"DECLARED RESOLUTION CADENCE: {expected_interval}")
    print("=" * 95)

    if not data_path.is_dir():
        print(f"\nERROR: Data directory does not exist: {data_path.resolve()}")
        return False

    provider = CsvEquityDataProvider(data_dir=data_path)
    all_valid = True

    print(
        f"\n{'Symbol':<8} {'Status':<10} {'Rows':<8} {'Start Date':<12} {'End Date':<12} "
        f"{'RTH Cov%':<10} {'Miss Min':<10} {'Gaps(>5d)':<11} {'Dupes':<6} "
        f"{'Hash (SHA256:8)':<16} {'Adjustment':<15}"
    )
    print("-" * 115)

    for sym in symbols:
        sym_upper = sym.upper()
        try:
            bars = provider.load_bars(sym_upper)
            prov = provider.get_provenance(sym_upper)
            val = validate_symbol_bars(
                sym_upper, bars, expected_interval=expected_interval
            )

            status = "VALID" if val.is_valid else "INVALID"
            if not val.is_valid:
                all_valid = False

            start_str = bars[0].timestamp.strftime("%Y-%m-%d")
            end_str = bars[-1].timestamp.strftime("%Y-%m-%d")
            short_hash = prov.file_sha256[:12]

            print(
                f"{sym_upper:<8} {status:<10} {len(bars):<8} {start_str:<12} {end_str:<12} "
                f"{val.rth_coverage_pct:<10.1f} {val.missing_minute_slots:<10} "
                f"{val.calendar_gaps_count:<11} {val.duplicates_count:<6} {short_hash:<16} "
                f"{prov.adjustment_status:<15}"
            )

            if val.errors:
                print(f"   Errors for {sym_upper}: {val.errors}")
            if val.warnings:
                for w in val.warnings:
                    print(f"   Warning [{sym_upper}]: {w}")

        except HistoricalDataMissingError as e:
            print(
                f"{sym_upper:<8} {'MISSING':<10} {'-':<8} {'-':<12} {'-':<12} "
                f"{'-':<6} {'-':<6} {'-':<16} {'-'}"
            )
            print(f"   Missing file: {e}")
            all_valid = False
        except Exception as e:
            print(
                f"{sym_upper:<8} {'ERROR':<10} {'-':<8} {'-':<12} {'-':<12} "
                f"{'-':<6} {'-':<6} {'-':<16} {'-'}"
            )
            print(f"   Load error: {e}")
            all_valid = False

    print("=" * 95)
    if all_valid:
        print("RESULT: ALL REQUIRED SYMBOLS PRESENT AND VALID.")
    else:
        print("RESULT: DATA VALIDATION FAILED. ONE OR MORE REQUIRED SYMBOLS MISSING OR INVALID.")

    return all_valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical Data Doctor & Integrity Checker")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to config YAML"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing historical CSVs",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    symbols = cfg.strategy.universe
    if cfg.strategy.two_x_etfs:
        symbols = symbols + cfg.strategy.two_x_etfs

    success = run_data_doctor(
        data_dir=args.data_dir,
        symbols=symbols,
        expected_interval=cfg.strategy.bar_interval,
    )
    sys.exit(0 if success else 1)



if __name__ == "__main__":
    main()
