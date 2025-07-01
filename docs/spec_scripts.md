## MirAI Trade – Script & Directory Specification

> **バージョン**: 2025‑06‑28（`main` ブランチ最新）
> このドキュメントは *apps/、configs/、docs/ ディレクトリ以下* の全 Python スクリプトと補助ファイルの構造・責務を一覧化したものです。ソースツリーを俯瞰しやすいよう **ディレクトリ → モジュール → 関数/クラス** の粒度で整理しています。

---

### 1. ルート構成

```
MirAI-_Trade/
├── .gitignore            # 生成物・env 除外
├── README.md             # 運用ガイド & インストール手順
├── configs/              # 設定ファイル（必ず config.py 経由で参照）
│   └── config.yaml
├── app/                  # アプリ本体
│   ├── core/             # 設定ロード & 共通ユーティリティ
│   ├── data/             # J‑Quants API フェッチャ群
│   ├── backtest/         # バックテスト一式（← **改修対象**）
│   ├── scoring/          # スコア計算モジュール（← **改修対象**）
│   ├── utils/            # 汎用フィルタ / 補助関数
│   └── main.py           # 旧スコアリング CLI（score_stocks.py を呼び実売買）
├── docs/                 # ドキュメント
└── tests/                # pytest（自動テスト）
```

---

### 2. configs/

| ファイル            | 主なキー                                                              | 説明                                                            |
| --------------- | ----------------------------------------------------------------- | ------------------------------------------------------------- |
| **config.yaml** | `jquants.base_url` / `jquants.endpoints.*``logging.*``database.*` | エンドポイント URL と全アプリ設定を集中管理。**スクリプトは直接読まず、必ず **\`\`** を経由すること。** |

---

### 3. app/core/

| モジュール              | 主な API                           | 役割                                                                        |
| ------------------ | -------------------------------- | ------------------------------------------------------------------------- |
| `config.py`        | `load_config(path) -> AppConfig` | Pydantic で `config.yaml` を読み取り、`cfg.jquants.endpoints.<name>` 形式で参照可能にする。 |
| `logger.py` *(省略)* | `get_logger(name)`               | 既定フォーマットのロガー生成。                                                           |

---

### 4. app/data/（J‑Quants フェッチャ）

> **方針**: 1 API = 1 `*_fetcher.py` が原則。現在はバックテストの都合で `premium_temp_fetcher.py` に先物四本値・信用週末残高・空売り残高・投資主体フローの **4 API** を暫定集約しているが、**実運用前に** それぞれ
> `futures_fetcher.py`, `weekly_margin_interest_fetcher.py`, `short_positions_fetcher.py`, `trades_spec_fetcher.py`
> へ分割予定。

| ファイル                      | 公開関数                                             | 取得 API                           | メモ                                                    |
| ------------------------- | ------------------------------------------------ | -------------------------------- | ----------------------------------------------------- |
| `daily_quotes_fetcher.py` | `get_daily_quotes`                               | `/v1/prices/daily_quotes`        | 日足 OHLCV 一括取得。                                        |
| `listed_info_fetcher.py`  | `get_listed_info`                                | `/v1/listed/info`                | 上場銘柄マスタ。                                              |
| `trading_days_fetcher.py` | `get_latest_trading_days(cfg, id_tok, lg, days)` | `/v1/markets/trading_calendar`   | **営業日確定 API**。`holidaydivision=="1"` を営業日と判定。自前計算は禁止。 |
| `premium_temp_fetcher.py` | `fetch_premium_temp`                             | `/v1/derivatives/futures` ほか 3 本 | プレミアムプラン API を 1 度に取得する暫定版。（先物空行ガードあり）                |

> **注意**: データ取得は *必ず* ここを経由し、スクリプト内で HTTP リクエストを直書きしない。

---

### 5. app/backtest/（改修範囲）

| モジュール                   | 主な関数                                                  | 役割 / フロー                                                                                                              |
| ----------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `add_derived_cols.py`   | `add_derived_cols(df)``main()`                        | - `price_ohlcv.csv` へ派生指標を追加- `trading_days_fetcher` で営業日取得 → プレミアム pkl をマージ- **先物 NK225F ギャップ** を `NK225_gap` 列として生成 |
| `backtest_runner.py`    | `run_backtest(df_price, df_info, coeffs, top_n)`      | 1 日分スコア計算→売買ルール→損益計算。                                                                                                 |
| `param_search.py`       | `_run_backtest_coarse` / `_run_backtest_fine``main()` | `joblib.Parallel` で係数グリッド探索。（並列数は `config.BACKTEST_N_JOBS` or CPU コア数）                                                |
| `metrics.py`            | `calc_sharpe()`, `max_drawdown()`                     | バックテスト統計。                                                                                                             |
| `generate_price_csv.py` | 補助スクリプト                                               | J‑Quants 日足をローカル CSV にキャッシュ。                                                                                          |

---

### 6. app/scoring/

| モジュール         | 公開関数            | 説明 |
| ------------- | --------------- | -- |
| `score_up.py` | **新スコアリングロジック** |    |

```
Score_up = (Vol_5 / Vol_20)
         * (ATR_5 / ATR_20)
         * (ATR_3 / ATR_10) ** 1.6
         * PullUp ** d                # PullUp = (Close₋1−Low₋1)/(High₋1−Low₋1)+0.5
         * max(0, Momentum_3_pos) ** c
         * (1 / log1p(1+Range_yesterday) ** 2.2)
         * (1 + (Close > MA_5))       # 当日陽線で×2
         * (1 + NK225_gap.clip(-0.02,0.02))
         * exp(-(LongShortRatio-1))   # 個人過熱を減点
         * (1 + ShortInc.clip(0,0.3)) # 踏み上げ加点
         * (1 + tanh(ForeignFlow3 / 1e8))
```

\| `score_stocks.py` | 旧ロジック (main.py から実運用中) | 旧式 `RANK(Vol_5 * ATR_5 * Range_yesterday)` | 旧ロジック (main.py から呼び出し実運用中) | 旧式 `RANK(Vol_5*ATR_5*Range_yesterday)`

---

### 7. docs/

`docs/spec_overview.md` … システム全体の概観。*本ドキュメント(**`docs/spec_scripts.md`**) はスクリプト詳細にフォーカス。*

---

## 8. 開発・運用ルール（README とテンプレートの要点）

1. \*\*営業日判定は必ず \*\*\`\`。
2. **API エンドポイントは **`** → **`** 経由**。
3. **改修対象は **`** と **`** のみ**。
4. `.env` / Secret キーは **コード・チャットとも貼り付け禁止**。
5. バックテスト結果（CSV, TXT）は `backtest_data/`, `backtest_results/` に出力し、Git にコミットしない。

---

## 9. TODO

* **フェッチャ正式分割**: `premium_temp_fetcher` を 4 ファイルに分離し、CI で個別 API テストを走らせる。
* **CI**: GitHub Actions で `pytest` + `param_search --dry-run` を PR ごとに実行。
* **ドキュメント統合**: `docs/spec_overview.md` と本書を mkdocs または mdBook で公開。

---

*以上*
本仕様書は開発者全員が “今どこを直せばよいか” を 5 分で掴めることを目標にしています。
