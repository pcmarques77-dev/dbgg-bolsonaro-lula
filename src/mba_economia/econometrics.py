"""Regressões exploratórias sobre o painel Focus (statsmodels)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import adfuller
from scipy.stats import f

logger = logging.getLogger(__name__)

DEFAULT_DEP_VAR = "ipca_med12m"
DEFAULT_REGRESSORS = (
    "dummy_lula",
    "dummy_pandemia",
    "vix",
    "commodities",
)


@dataclass(frozen=True)
class EconometricsResult:
    """Resultados da rodada OLS + testes auxiliares."""

    dep_var: str
    regressors: tuple[str, ...]
    n_obs: int
    ols_summary: str
    coef_table: pd.DataFrame
    adf: pd.DataFrame
    diagnostics: pd.DataFrame
    chow_table: pd.DataFrame | None = None


def prepare_regression_sample(
    panel: pd.DataFrame,
    *,
    dep_var: str = DEFAULT_DEP_VAR,
    regressors: tuple[str, ...] = DEFAULT_REGRESSORS,
) -> pd.DataFrame:
    """Remove linhas com NaN nas variáveis do modelo (sem imputação)."""
    real_dep = "selic_mediana_pct" if dep_var == "taylor_rule" else dep_var
    cols = [real_dep, *regressors]
    missing = [c for c in cols if c not in panel.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no painel: {missing}")
    sample = panel[cols].copy()
    for c in cols:
        sample[c] = pd.to_numeric(sample[c], errors="coerce")
    return sample.dropna(how="any").reset_index(drop=True)


def _run_adf(series: pd.Series, label: str) -> dict[str, float | str]:
    clean = series.dropna()
    if len(clean) < 8:
        return {
            "serie": label,
            "adf_stat": np.nan,
            "p_value": np.nan,
            "n_obs": float(len(clean)),
            "conclusao_5pct": "amostra_insuficiente",
        }
    stat, pval, *_ = adfuller(clean, autolag="AIC")
    conclusao = "rejeita_H0_raiz_unitária" if pval < 0.05 else "não_rejeita_H0_raiz_unitária"
    return {
        "serie": label,
        "adf_stat": float(stat),
        "p_value": float(pval),
        "n_obs": float(len(clean)),
        "conclusao_5pct": conclusao,
    }


def _ols_diagnostics(
    fitted: sm.regression.linear_model.RegressionResultsWrapper,
) -> pd.DataFrame:
    resid = fitted.resid
    exog = fitted.model.exog
    bp_stat, bp_p, _, _ = het_breuschpagan(resid, exog)
    dw = durbin_watson(resid)
    jb_stat, jb_p, skew, kurt = jarque_bera(resid)
    rows = [
        ("breusch_pagan_stat", bp_stat, "heterocedasticidade (H0: homocedasticidade)"),
        ("breusch_pagan_pvalue", bp_p, ""),
        ("durbin_watson", dw, "autocorrelação serial (~2 sem AR(1))"),
        ("jarque_bera_stat", jb_stat, "normalidade dos resíduos"),
        ("jarque_bera_pvalue", jb_p, ""),
        ("resid_skew", skew, ""),
        ("resid_kurtosis", kurt, ""),
    ]
    return pd.DataFrame(rows, columns=["teste", "valor", "nota"])


def run_panel_ols(
    panel: pd.DataFrame,
    *,
    dep_var: str = DEFAULT_DEP_VAR,
    regressors: tuple[str, ...] = DEFAULT_REGRESSORS,
) -> EconometricsResult:
    """OLS com constante: expectativa IPCA 12m ~ dummies + controles globais."""
    sample = prepare_regression_sample(panel, dep_var=dep_var, regressors=regressors)
    if len(sample) < len(regressors) + 2:
        raise ValueError(
            f"Amostra insuficiente para OLS ({len(sample)} obs.; mínimo ~{len(regressors) + 2}).",
        )

    real_dep = "selic_mediana_pct" if dep_var == "taylor_rule" else dep_var
    y = sample[real_dep].rename(dep_var)
    x = sm.add_constant(sample[list(regressors)], has_constant="add")
    model = sm.OLS(y, x, missing="drop")
    # Usa Newey-West HAC covariance com 4 lags
    fitted = model.fit(cov_type="HAC", cov_kwds={"maxlags": 4})

    adf_rows = [
        _run_adf(y, dep_var),
        *(_run_adf(sample[r], r) for r in regressors),
    ]
    adf_df = pd.DataFrame(adf_rows)

    coef = pd.DataFrame(
        {
            "coef": fitted.params,
            "std_err": fitted.bse,
            "t_stat": fitted.tvalues,
            "p_value": fitted.pvalues,
            "conf_low": fitted.conf_int()[0],
            "conf_high": fitted.conf_int()[1],
        },
    )
    coef.index.name = "variavel"

    diag = _ols_diagnostics(fitted)
    logger.info(
        "OLS %s ~ [%s]: n=%s, R²=%.4f",
        dep_var,
        ", ".join(regressors),
        len(sample),
        fitted.rsquared,
    )

    # Chow test calculation
    chow_table = None
    if "dummy_lula" in sample.columns:
        try:
            # Determine sub columns to test for structural break
            if "desancoragem_centro_12m" in regressors:
                sub_cols = ["desancoragem_centro_12m"]
            else:
                sub_cols = [r for r in regressors if r not in ["dummy_lula", "dummy_pandemia"]]
                
            k_sub = len(sub_cols) + 1  # count constant
            
            # Split data
            df_b = sample[sample["dummy_lula"] == 0]
            df_l = sample[sample["dummy_lula"] == 1]
            
            n1 = len(df_b)
            n2 = len(df_l)
            
            if n1 >= k_sub and n2 >= k_sub:
                real_dep = "selic_mediana_pct" if dep_var == "taylor_rule" else dep_var
                y_b = df_b[real_dep]
                X_b = sm.add_constant(df_b[sub_cols])
                res_b = sm.OLS(y_b, X_b).fit()
                ssr_b = res_b.ssr
                
                y_l = df_l[real_dep]
                X_l = sm.add_constant(df_l[sub_cols])
                res_l = sm.OLS(y_l, X_l).fit()
                ssr_l = res_l.ssr
                
                numerator = (fitted.ssr - (ssr_b + ssr_l)) / k_sub
                denominator = (ssr_b + ssr_l) / (n1 + n2 - 2 * k_sub)
                
                if denominator == 0:
                    chow_f = 0.0
                else:
                    chow_f = numerator / denominator
                    
                p_val = 1.0 - f.cdf(chow_f, k_sub, n1 + n2 - 2 * k_sub)
                conclusao = "quebra estrutural significante a 5%" if p_val < 0.05 else "não rejeita H0"
                
                chow_rows = [
                    ("chow_f_stat", chow_f, conclusao),
                    ("chow_n_bolsonaro", float(n1), ""),
                    ("chow_n_lula", float(n2), ""),
                    ("chow_params_count", float(k_sub), f"Variáveis analisadas: {', '.join(sub_cols)}"),
                ]
                chow_table = pd.DataFrame(chow_rows, columns=["teste", "valor", "nota"])
        except Exception as e:
            logger.warning(f"Erro ao calcular teste de Chow para {dep_var}: {e}")

    return EconometricsResult(
        dep_var=dep_var,
        regressors=regressors,
        n_obs=len(sample),
        ols_summary=fitted.summary().as_text(),
        coef_table=coef.reset_index(),
        adf=adf_df,
        diagnostics=diag,
        chow_table=chow_table,
    )


def write_econometrics_outputs(result: EconometricsResult, out_dir: Path) -> list[Path]:
    """Grava sumário OLS, coeficientes, ADF e diagnósticos em ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"econometria_ols_{result.dep_var}"
    paths: list[Path] = []

    summary_path = out_dir / f"{stem}_summary.txt"
    summary_path.write_text(result.ols_summary, encoding="utf-8")
    paths.append(summary_path)

    diag_path = out_dir / f"{stem}_diagnosticos.txt"
    diag_lines = [
        f"Modelo: {result.dep_var} ~ const + {', '.join(result.regressors)}",
        f"Observações: {result.n_obs}",
        "Covariância: HAC (erros robustos Newey-West maxlags=4 se HAC)",
        "",
        "=== Diagnósticos de resíduos ===",
        result.diagnostics.to_string(index=False),
        "",
        "=== ADF (Dickey-Fuller aumentado, autolag=AIC) ===",
        result.adf.to_string(index=False),
    ]
    if result.chow_table is not None:
        diag_lines.extend([
            "",
            "=== Teste de Quebra Estrutural de Chow (Bolsonaro vs. Lula 3) ===",
            result.chow_table.to_string(index=False),
        ])

    diag_path.write_text("\n".join(diag_lines), encoding="utf-8")
    paths.append(diag_path)

    coef_csv = out_dir / f"{stem}_coef.csv"
    result.coef_table.to_csv(coef_csv, index=False, decimal=",", sep=";")
    paths.append(coef_csv)

    adf_csv = out_dir / f"{stem}_adf.csv"
    result.adf.to_csv(adf_csv, index=False, decimal=",", sep=";")
    paths.append(adf_csv)

    if result.chow_table is not None:
        chow_csv = out_dir / f"{stem}_chow.csv"
        result.chow_table.to_csv(chow_csv, index=False, decimal=",", sep=";")
        paths.append(chow_csv)

    return paths
