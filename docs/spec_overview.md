### 2025-06-26

# MirAI Trade — 概念 & 再開フロー（抜粋版）

## 0. セッション再開フロー

1. `git pull`
2. `git checkout -b <feature>`
3. **改修対象**

   * `app/backtest/*`
   * `app/scoring/score_up.py`
4. `git push` → PR → **ChatGPT に PR 番号** を貼る（レビュー）
5. Merge → `git pull`
6. バックテスト再実行

   ```bash
   python -m app.backtest.add_derived_cols
   python -m app.backtest.param_search
   ```

## 1. ディレクトリ抜粋

```text
app/
├─ core/         # config / logger
├─ data/         # J-Quants fetchers
├─ scoring/      # score_up.py
├─ backtest/     # add_derived_cols.py / param_search.py / runner
└─ exporters/    # Excel output
backtest_data/   # 自動生成 (.gitignore)
backtest_results/# 自動生成 (.gitignore)
```

## 2. 基本ポリシー（追加ガード）

* **取引営業日** は必ず `app/data/trading_days_fetcher.py` を呼び出す
  自前で算出しない
* **API エンドポイント** は `configs/config.yaml` に定義し
  コードからは `config.py` 経由で取得
* 改修ファイルは *backtest* / *scoring* のみ。
  他ディレクトリは参照専用
* `.env` / API キーをチャットに貼らない

> 詳細仕様は各サブスクリプトの docstring を参照