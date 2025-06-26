"""app/backtest/param_search.py

2 段階グリッドサーチで Score_up の (a,b,c,d, TopN) を最適化する。
粗探索: c,d,TopN  → 細探索: a,b,TopN

- 指標は metrics.calc_metrics()
- 合格ラインを満たしたものの中で Sharpe 最大を最適解とする
- 結果を backtest_results/param_report.txt に保存
"""

from __future__ import annotations

from itertools import product
from joblib import Parallel, delayed
import os
from pathlib import Path
import pandas as pd
from logging import getLogger, basicConfig, WARNING

import yaml              # ← まだ無ければ追加


from app.core.config import load_config
from app.data.jquants_signin import get_refresh_token, get_id_token
from app.data.listed_info_fetcher import fetch_listed_info
from app.backtest.add_derived_cols import add_derived_cols  # ensure derived cols exist if needed
from app.backtest.backtest_runner import run_backtest
from app.backtest.metrics import calc_metrics

INPUT_CSV = Path("backtest_data/price_ohlcv_derived.csv")
REPORT_TXT = Path("backtest_results/param_report.txt")

basicConfig(level=WARNING, format="%(levelname)s  %(message)s")
logger = getLogger("param_search")

# ------------------------------- 合格ライン ------------------------------ #
THRESHOLDS = {
    "mu": 0.05,       # +5 %
    "win_rate": 0.55, # 55 %
    "sharpe": 1.5,
    "max_dd": -0.15,  # drawdown ≤ -15 % (値は負)
}

# ------------------------------- グリッド定義 ----------------------------- #
COARSE_C    = [0.6,0.8,1.0,1.2,1.4,1.6,1.8,2.0,2.4,2.8]
COARSE_D    = [0.4,0.6,0.8,1.0,1.2,1.4,1.6,1.8]
COARSE_TOPN = [10, 12, 15]

FINE_A = [0.8, 0.9, 1.0, 1.1, 1.2]
FINE_B = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
FINE_TOPN   = [10, 12]

# ------------------------------- ヘルパ ---------------------------------- #

# --------------------------------------------------------------
# 並列数を自動決定（config.yaml > 物理コア）
# --------------------------------------------------------------
def _suggest_n_jobs() -> int:
    """
    Ryzen 9 5950X 用 推奨並列数を返す。

    1. configs/config.yaml に BACKTEST_N_JOBS があればそれを優先
    2. 無ければ物理コア数（16）を利用
    """
    try:
        with open("configs/config.yaml", "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
            if "BACKTEST_N_JOBS" in raw and raw["BACKTEST_N_JOBS"]:
                return int(raw["BACKTEST_N_JOBS"])
    except FileNotFoundError:
        pass  # ファイルが無ければ物理コアで代用

    logical = os.cpu_count() or 1        # 5950X は 32 論理
    return logical // 2 or 1             # 16 物理。最低でも 1

# --------------------------------------------------------------
# Helper wrappers for joblib (need top‑level picklable funcs)
# --------------------------------------------------------------
def _run_backtest_coarse(price_df, info_df, c, d, top):
    res = run_backtest(price_df, info_df, (1, 1, c, d), top)
    m   = calc_metrics(res["Ret"])
    m.update({"a": 1, "b": 1, "c": c, "d": d, "TopN": top})
    return m

def _run_backtest_fine(price_df, info_df, a, b, c, d, top):
    res = run_backtest(price_df, info_df, (a, b, c, d), top)
    m   = calc_metrics(res["Ret"])
    m.update({"a": a, "b": b, "c": c, "d": d, "TopN": top})
    return m

def _meets_threshold(m: dict[str, float]) -> bool:
    return (
        m["mu"] >= THRESHOLDS["mu"] and
        m["win_rate"] >= THRESHOLDS["win_rate"] and
        m["sharpe"] >= THRESHOLDS["sharpe"] and
        m["max_dd"] >= THRESHOLDS["max_dd"]
    )

# ------------------------------- メイン ---------------------------------- #

def main() -> None:
    if not INPUT_CSV.exists():
        logger.error("Derived CSV not found: %s", INPUT_CSV)
        return
    price_df = pd.read_csv(INPUT_CSV, parse_dates=["Date"])

    cfg = load_config("configs/config.yaml")
    refresh = get_refresh_token(cfg, logger)
    id_tok = get_id_token(cfg, refresh, logger)
    info_df = fetch_listed_info(cfg, id_tok, logger)

    best = None  # type: dict[str, float] | None

    # --- Step A: 粗探索 (c,d) ------------------------------------------ #
    n_jobs = _suggest_n_jobs()
    coarse_results = Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(_run_backtest_coarse)(price_df, info_df, c, d, top)
        for c, d, top in product(COARSE_C, COARSE_D, COARSE_TOPN)
    )
    coarse_sorted = sorted(coarse_results, key=lambda x: x["sharpe"], reverse=True)[:3]

    # --- Step B: 細探索 (a,b) ------------------------------------------ #
    fine_results = []
    for param in coarse_sorted:
        c, d = param["c"], param["d"]
        fine_batch = Parallel(n_jobs=n_jobs, verbose=10)(
            delayed(_run_backtest_fine)(price_df, info_df, a, b, c, d, top)
            for a, b, top in product(FINE_A, FINE_B, FINE_TOPN)
        )
        for m in fine_batch:
            fine_results.append(m)
            if _meets_threshold(m):
                if best is None or m["sharpe"] > best["sharpe"]:
                    best = m
                    logger.info("New best: %s", best)

    REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_TXT.open("w", encoding="utf-8") as f:
        f.write("### Param Search Report\n")
        f.write(f"Best Params: {best}\n\n")
        f.write("Top 10 by Sharpe:\n")
        for row in sorted(fine_results, key=lambda x: x["sharpe"], reverse=True)[:10]:
            f.write(str(row) + "\n")
    logger.info("Report saved: %s", REPORT_TXT)

    # ここから追記  ▼▼▼
    if best:
        logger.info("Re-running backtest with BEST params for CSV/PNG …")
        best_coeffs = (best["a"], best["b"], best["c"], best["d"])
        best_topn   = best["TopN"]

        res_best = run_backtest(price_df, info_df, best_coeffs, best_topn)

        out_dir = Path("backtest_results")
        out_dir.mkdir(exist_ok=True, parents=True)

        csv_path = out_dir / "results_90d.csv"
        res_best.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("Saved %s", csv_path)

        # 資産曲線
        import matplotlib.pyplot as plt
        equity = (1 + res_best["Ret"]).cumprod()
        plt.figure()
        plt.plot(res_best["Date"], equity)
        plt.title("Equity Curve (Best Params)")
        plt.xlabel("Date"); plt.ylabel("Equity")
        plt.grid(True)
        plt.savefig(out_dir / "equity_curve.png", dpi=120, bbox_inches="tight")
        plt.close()
    # 追記ここまで  ▲▲▲

if __name__ == "__main__":
    main()
