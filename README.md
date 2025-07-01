# MirAI\_Trade

> **日本株スキャルピング／デイトレード向けの 90 日バックテスト & スクリーニングツール**\
> J‑Quants API + Python 3.12。ソースコードは **GitHub** で一元管理し、ChatGPT にはアップロードしません。
> **詳細仕様は** [`Docs/spec_overview.md`](docs/spec_overview.md) を参照

---

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [ディレクトリ構成](#ディレクトリ構成)
- [クイックスタート](#クイックスタート)
- [日常ワークフロー](#日常ワークフロー)
- [主要スクリプト](#主要スクリプト)
- [バックテストパラメータ](#バックテストパラメータ)
- [コントリビュート](#コントリビュート)
- [ライセンス](#ライセンス)

---

## プロジェクト概要

1. 寄り付き前に **Score\_up** を計算し、東証（プライム／スタンダード／グロース）の上位 40 銘柄を抽出。
2. 90 営業日分の **日足データでバックテスト**（寄付き買い→引け売り、コスト 0.1 %）。
3. パラメータグリッドサーチで期待値（μ/Sharpe）を最適化。
4. 依存は **pandas / joblib / openpyxl** のみ。Docker 不要、軽量設計。

---

## ディレクトリ構成

```text
MirAI_Trade/
├─ app/
│  ├─ core/         # 設定 & ロガー
│  ├─ data/         # J‑Quants API ラッパ
│  ├─ backtest/     # add_derived_cols.py / backtest_runner.py / param_search.py
│  ├─ scoring/      # score_up.py（スコア計算）
│  └─ exporters/    # Excel / DB 出力
├─ backtest_data/   # 生成される派生 CSV（.gitignore）
├─ backtest_results/ # 生成されるレポート（.gitignore）
├─ configs/         # YAML & .env サンプル
└─ README.md        # ← このファイル
```

> `backtest_data/` と `backtest_results/` は **自動生成フォルダ**。Git に含めません。

---

## クイックスタート

```bash
# 1) クローン & 仮想環境
$ git clone https://github.com/muthunohara/MirAI_Trade.git
$ cd MirAI_Trade
$ python -m venv venv && source venv/bin/activate   # Windows は venv\Scripts\activate
$ pip install -r requirements.txt

# 2) J‑Quants 認証情報を設定
$ cp configs/config.yaml.sample configs/config.yaml
$ cp .env.sample .env   # JQ_EMAIL / JQ_PASSWORD を入力

# 3) 90 日バックテスト実行（シングルスレッド）
$ python -m app.backtest.add_derived_cols
$ python -m app.backtest.param_search

# 4) 並列化（8 コア）したい場合
$ pip install joblib
# param_search.py を編集 → Parallel(n_jobs=8)
```

---

## 日常ワークフロー（GitHub × ChatGPT）

```text
1) git pull                      # main を同期
2) git checkout -b feat/<topic>  # ブランチ作成
3) VS Code で編集・保存
4) git add + commit + push
5) GitHub → "Compare & pull request"
6) PR 番号を ChatGPT に共有 → AI レビュー
7) Merge 後 git pull            # main 更新
8) python -m app.backtest.add_derived_cols
   python -m app.backtest.param_search
```

> **ソースを ChatGPT に直接アップロードしない**。PR 番号や差分リンクで共有してください。

---

## 主要スクリプト

| パス                                 | 役割                                    |
| ---------------------------------- | ------------------------------------- |
| `app/backtest/add_derived_cols.py` | Vol\_5 / ATR\_5 などの派生指標を付与            |
| `app/scoring/score_up.py`          | Score\_up 計算 & ETF/REIT 除外・±10 % フィルタ |
| `app/backtest/backtest_runner.py`  | 1 日分のバスケットバックテスト (コスト 0.1 %)          |
| `app/backtest/param_search.py`     | グリッドサーチ + レポート生成                      |

---

## バックテストパラメータ（デフォルト）

| パラメータ        | 範囲 / 値             | 説明                        |
| ------------ | ------------------ | ------------------------- |
| TopN         | 10 / 12 / 15       | バスケット銘柄数                  |
| c (Momentum) | 0.6 – 2.8 (0.2 刻み) | モメンタム係数                   |
| d (PullUp)   | 0.4 – 1.8 (0.2 刻み) | レンジ位置係数                   |
| Cost         | 0.1 % (往復)         | `backtest_runner.py` 内で調整 |

合格基準：**μ ≥ +5 % • 勝率 ≥ 55 % • Sharpe ≥ 1.5 • MaxDD ≤ 15 %**

---

## コントリビュート

1. フォーク or ブランチ作成 `feat/` / `fix/`
2. **Google スタイル docstring & 型ヒント** を付与
3. `ruff` / `black` で整形
4. 必要なら pytest で単体テスト追加
5. PR タイトル：`feat: …` / `fix: …`、本文に目的を 1 行

---

## ライセンス

Private / Educational — All rights reserved.

