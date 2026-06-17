"""Cross-platform smoke test for CI (and local sanity).

Pure-Python checks that don't need a browser or network:
  - DataProcessor.process_fidc_data produces the 9-column tidy frame
  - subclass_matches resolves codes and class names, blank = keep all

Run:  python tests/smoke_test.py   (exits non-zero on failure)
"""

import os
import sys

# Allow running from the repo root or the tests/ dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor import DataProcessor  # noqa: E402
from stealth_scraper import subclass_matches  # noqa: E402


def test_process_fidc_data():
    sample = [
        {
            "CNPJ": "53.189.745/0001-07",
            "Status": "Success",
            "subclasses": [
                {
                    "subclasse_name": "CREDITO CONSIGNADO PREFIXADO FC FIDC",
                    "subclasse_code": "S0000762296",
                    "periodic_data": [
                        {
                            "Data competência": "01/06/2026",
                            "Valor patrimônio líquido": "R$ 79.148.239,98",
                            "Valor cota": "R$ 439,648005",
                            "Valor volume total de aplicação": "R$ 0,00",
                            "Valor volume total de resgates": "R$ 0,00",
                            "Número total de cotistas": "1804",
                        }
                    ],
                }
            ],
        }
    ]
    df = DataProcessor().process_fidc_data(sample)
    assert df.shape == (1, 9), f"unexpected shape {df.shape}"
    assert list(df.columns)[:3] == ["CNPJ", "Subclasse", "Código"], list(df.columns)
    # empty input → empty frame with the same columns
    empty = DataProcessor().process_fidc_data(
        [{"CNPJ": "x", "Status": "No data", "subclasses": []}]
    )
    assert empty.shape == (0, 9), empty.shape


def test_subclass_matches():
    subs = [
        {"subclasse_name": "FIDC SUBCLASSE SENIOR", "subclasse_code": "S0000762290"},
        {"subclasse_name": "FIDC SUBCLASSE B", "subclasse_code": "S0000762296"},
        {"subclasse_name": "FIDC SUBCLASSE A", "subclasse_code": "S0000762300"},
    ]
    assert [s for s in subs if subclass_matches("S0000762296", s)][0][
        "subclasse_code"
    ] == "S0000762296"
    assert [s for s in subs if subclass_matches("50000762296", s)][0][
        "subclasse_code"
    ] == "S0000762296"
    assert [s for s in subs if subclass_matches("SUBCLASSE SENIOR", s)][0][
        "subclasse_code"
    ] == "S0000762290"
    assert [s for s in subs if subclass_matches("SUBCLASSE A", s)][0][
        "subclasse_code"
    ] == "S0000762300"
    assert all(subclass_matches("", s) for s in subs), "blank desired must keep all"


def main():
    test_process_fidc_data()
    test_subclass_matches()
    print("smoke tests OK")


if __name__ == "__main__":
    main()
