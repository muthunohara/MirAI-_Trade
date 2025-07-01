# MirAI Trade

> **日本株スキャルピング AI** — 日足 × プライスアクションで寄付→引けを狙う自動スクリーニング＆裁量ハイブリッド手法。
> このリポジトリは *バックテスト → シグナル生成 → 本番実行* を一元管理します。

---

## 📚 ドキュメント早見表

| ドキュメント                                           | 目的                        | 備考             |
| ------------------------------------------------ | ------------------------- | -------------- |
| [`docs/spec_overview.md`](docs/spec_overview.md) | プロジェクト全体のモジュール相関図         | まずはここから 🗺️    |
| [`docs/spec_scripts.md`](docs/spec_scripts.md)   | 各 *.py* の責務・入出力詳細         | 関数単位で深掘り⚙️     |
| [`docs/dev_ops.md`](docs/dev_ops.md)             | pre‑commit / CI / 依存バージョン | 開発環境セットアップ🔧   |
| [`docs/backtest_tips.md`](docs/backtest_tips.md) | パラメータサーチ手順・指標             | 勝率55 % へ最短で 🚀 |

> **NOTE** : 詳細仕様は上記 docs に集約しています。README では *重複説明を省略* し、入口と全体像だけ提供します。

---

## 🏗️ ディレクトリ概要 (抜粋)

```
MirAI-_Trade/
├─ app/
│  ├─ data/                 # J‑Quants API ラッパ (1 API = 1 *_fetcher.py*)
│  │   └─ premium_temp_fetcher.py  # ← 先物ほか4APIを暫定集約
│  ├─ scoring/
│  │   ├─ score_stocks.py   # 旧スコアリング (本番)
│  │   └─ score_up.py       # 新スコアリング (βテスト)
│  └─ backtest/             # add_derived_cols → backtest_runner → param_search
├─ configs/config.yaml      # API エンドポイント・定数
├─ docs/                    # 仕様ドキュメント（上表）
└─ backtest_data/, backtest_results/  # 生成物 (git-ignore)
```

---

## 🚀 クイックスタート

```bash
# 1. 環境構築
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pre-commit install            # 推奨

# 2. プレミアムデータ取得 (直近60営業日)
python make_premium_pickle.py

# 3. 派生列生成 & バックテスト
python -m app.backtest.add_derived_cols
python -m app.backtest.param_search

# 4. 実運用シグナル
python main.py                # 旧ロジック
```

> **取引営業日** は必ず `app/data/trading_days_fetcher.py` を通じて取得します（自前カレンダー計算禁止）。

---

## 🛠️ メンテナンスルール

* **1 API = 1 *\_fetcher.py*** が原則。`premium_temp_fetcher.py` は暫定。実運用前に `futures_fetcher.py` などへ分割予定。
* 改修対象は基本 `app/backtest/*` と `app/scoring/score_up.py` のみ。他モジュールの破壊的変更は PR で相談。
* `.env` や API キーは絶対にコミットしない。

---

© 2025 MirAI Trade Project

---

## 日常ワークフロー（GitHub × ChatGPT）

```text
1) git pull                          # main を同期
2) git checkout -b feat/<topic>      # 変更用ブランチを作成
3) VS Code で編集・保存             # 生成物 (backtest_data/, backtest_results/) は無視
4) git add + commit + push           # push で GitHub に反映
5) GitHub → "Compare & pull request"  # PR 作成
6) PR 番号を ChatGPT に共有          # AI コードレビュー (CI-pass + human review)
7) Merge 後 git pull                 # main を最新化
8) python make_premium_pickle.py     # 必要ならプレミアム pkl 更新（90営業日）
   python -m app.backtest.add_derived_cols
   python -m app.backtest.param_search  # 勝率/Sharpe を確認
```
