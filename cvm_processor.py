"""
CVM Quota Processor
Parses a downloaded inf_diario_fi CSV and filters it down to the requested
CNPJs, producing a tidy DataFrame: one row per CNPJ x subclasse x date.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

import config

logger = logging.getLogger(__name__)

# Mirrors DataProcessor.process_fidc_data's shape (CNPJ/Subclasse + the FIDC
# periodic columns) so output stays consistent with the ANBIMA path.
OUTPUT_COLUMNS = [
    "CNPJ",
    "Subclasse",
    "Data competência",
    "Valor cota",
    "Valor patrimônio líquido",
    "Valor volume total de aplicação",
    "Valor volume total de resgates",
    "Número total de cotistas",
]

_RENAME = {
    "cnpj": "CNPJ",
    "subclasse": "Subclasse",
    "date": "Data competência",
    "quota": "Valor cota",
    "patrim_liq": "Valor patrimônio líquido",
    "captc_dia": "Valor volume total de aplicação",
    "resg_dia": "Valor volume total de resgates",
    "nr_cotst": "Número total de cotistas",
}


def load_quotas(csv_path: Path, cnpjs: List[str]) -> pd.DataFrame:
    """Read the raw CVM CSV and filter to `cnpjs`.

    Returns one row per (CNPJ, ID_SUBCLASSE, date). Some funds have several
    subclasses sharing the same CNPJ+date with different quotas, so the
    subclass id is kept as a disambiguator rather than collapsed away.
    """
    cols = config.CVM_COLUMNS
    wanted = set(cols.values())

    logger.info("Reading %s", csv_path)
    df = pd.read_csv(
        csv_path,
        sep=";",
        usecols=lambda c: c in wanted,
        dtype={cols["cnpj"]: str, cols["subclasse"]: str},
    )

    cnpj_set = {c.strip() for c in cnpjs}
    df = df[df[cols["cnpj"]].isin(cnpj_set)].copy()
    if df.empty:
        logger.warning(
            "None of the %d requested CNPJ(s) were found in %s", len(cnpj_set), csv_path
        )

    df.rename(columns={cols[k]: v for k, v in _RENAME.items()}, inplace=True)
    df["Subclasse"] = df["Subclasse"].fillna("")
    df = df.sort_values(["CNPJ", "Subclasse", "Data competência"]).reset_index(
        drop=True
    )

    # Cosmetic: real dd/mm/yyyy date (CVM ships ISO strings) + numeric columns.
    # CVM VL_QUOTA is already a plain decimal (dot separator), so a straight
    # numeric coercion is all that's needed — no "R$" here.
    from data_processor import to_date

    df["Data competência"] = df["Data competência"].map(to_date)
    for col in (
        "Valor cota",
        "Valor patrimônio líquido",
        "Valor volume total de aplicação",
        "Valor volume total de resgates",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Número total de cotistas"] = pd.to_numeric(
        df["Número total de cotistas"], errors="coerce"
    ).astype("Int64")

    return df[OUTPUT_COLUMNS]


def missing_cnpjs(df: pd.DataFrame, cnpjs: List[str]) -> List[str]:
    """CNPJs that were requested but never matched a row — usually a typo or
    a fund not registered with CVM under that exact CNPJ."""
    found = set(df["CNPJ"].unique())
    return [c for c in cnpjs if c.strip() not in found]
