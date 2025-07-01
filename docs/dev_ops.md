## MirAI Trade – Dev Ops / CI ガイド

> **目的** : 開発体験を壊さずにコード品質を自動担保し、実運用で事故らないパイプラインを用意する。
> （全手順は **Windows 11 + VS Code** を想定 / WSL 2 でも同じ）

---

### 1. 推奨ツール & バージョン

| ツール            | バージョン               | 用途                             |
| -------------- | ------------------- | ------------------------------ |
| Python         | 3.12.x (公式 CPython) | ランタイム                          |
| pipx           | 最新                  | CLI 系ツールをユーザ環境に隔離インストール        |
| `pre-commit`   | 3.x                 | ローカル静的解析 & auto‑fix            |
| `ruff`         | 0.4.\*              | Lint & import sort (flake8 互換) |
| `black`        | 24.4 以降             | フォーマッタ（PEP 8 準拠）               |
| GitHub Actions | ubuntu‑latest       | CI ランナー                        |

---

### 2. フォーマッタ & Lint 設定

```toml
# pyproject.toml（抜粋）
[tool.black]
line-length = 119
skip-string-normalization = true

[tool.ruff]
line-length = 119
select = ["E", "F", "I", "W", "B", "UP"]   # pep8, flake, import, warnings, bugbear, pyupgrade
ignore = ["E203", "W503"]                       # black と競合する項目
fix = true                                        # --fix 自動修正
```

* **black** と **ruff** の行長を 119 文字で統一。
* `ruff` は `--fix` を使い **import 並べ替え** も自動化 (isort 不要)。

---

### 3. pre‑commit フック

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: ["--fix"]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: end-of-file-fixer
```

#### インストール & 実行

```powershell
pipx install pre-commit
pre-commit install           # .git/hooks に symlink
# 既存ソースへ一括適用
pre-commit run --all-files   # ☆ 初回のみ 30–60 秒
```

---

### 4. GitHub Actions – CI パイプライン

`.github/workflows/ci.yml`

```yaml
ame: CI
on:
  push:
    branches: [ main, "feat/**" ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install ruff black pre-commit
      - name: Run linters & formatters
        run: |
          ruff --output-format=github --fix .
          black --check .
      - name: Run unit tests (placeholder)
        run: |
          echo "TODO: pytest once tests are ready"
```

* プッシュ & PR 作成で **ruff → black → pytest** を順に実⾏。
* `ruff --output-format=github` でアノテーションが PR 画⾯に表示。
* フォーマット失敗や Lint エラーがあるとジョブ失敗 → マージ不可。

---

### 5. 開発フロー Quick Start

1. `git checkout -b feat/<topic>`
2. コードを書く → VS Code が保存時に black を⾃動実⾏ (設定済み推奨)
3. `git add -u && git commit -m "feat: ..."`
4. **pre‑commit がローカルで強制的に Lint/Format**
5. `git push` → PR → GitHub Actions CI が再チェック
6. 緑✅ になったらレビュー → squash & merge → main へ

---

### 6. よくあるトラブルシューティング

| 症状                         | 対処                                                     |
| -------------------------- | ------------------------------------------------------ |
| `line too long` で ruff が失敗 | 文字列なら `# noqa: E501` を末尾に一時許可／もしくは長い URL を変数に切り出し      |
| black による import 並び替え違和感   | black は import ソートしない → 並び替えは ruff (isort) にお任せ        |
| pre‑commit が遅い             | `pre-commit.ci` を導入すると PR 時のみクラウドで実行可                  |
| Windows でシバン行 warning      | Git のコア設定 `git config --global core.autocrlf true` を推奨 |

---

これで **ローカル → pre‑commit → GitHub Actions** が一貫して同じルールで動くため、
「動くけどフォーマットが違う / Lint が通らず CI 落ちる」問題を根絶できます。
