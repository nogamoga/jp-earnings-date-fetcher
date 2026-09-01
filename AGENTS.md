# AGENTS.md

## セットアップ

- **Python >= 3.11** が必要。
- `pip install -e .` でインストール。テスト用: `pip install -e ".[dev]"`

## コマンド

- **決算データ取得**: `python -m jpx_earnings fetch --out docs/v1`
  - `docs/v1/events.json` と `docs/v1/manifest.json` を書き出す
  - `--replace` で既存の events.json にマージせず置き換え
  - CLIエイリアス: `jpx-earnings fetch`
- **株価マージ**: `python examples/merge_prices.py --prices prices.csv --events docs/v1/events.json --out merged.csv`
- **テスト**: `pytest`

## 構成

JPX「決算発表予定日」の月次 xlsx ファイルをスクレイピングし、マージ準備済み JSON を出力する単一パッケージ (`jpx_earnings/`)。

| モジュール | 役割 |
|--------|------|
| `fetch.py` | JPXインデクスをスクレイピング、 cohort xlsx ファイルのダウンロードとパースの調整 |
| `normalize.py` | コード正規化 (NFKC、ゼロ埋め)、四半期マッピング (FY/1Q/2Q/3Q)、日付パース (ISO 8601、Excel シリアル日付) |
| `store.py` | `events.json` (マージ済み重複排除配列) と `manifest.json` の読み書き |
| `cli.py` | `fetch` サブコマンド付き argparse |

エントリーポイント: `python -m jpx_earnings` → `cli.main()`

## 注意点

- **マージセマンティクス**: 同じ `(code, scheduled_date)` キーの行が存在する場合、**新規行が既存行を上書き**する。
- ラベルに「翌営業日」を含む xlsx リンクはスキップする (翌営業日更新情報であり cohort ファイルではない)。
- `map_fq()` は曖昧マッピング: 日本語テキスト ("本決算", "第１四半期", "中間") を処理。マップできないタイプ (例: "その他") はドロップされる。
- Excel シリアル日付は float/int で届くため、`parse_scheduled_date` で `date(1899, 12, 30) + days` で変換する。
- デフォルト出力ディレクトリは `docs/v1` (CLI の `--out` でハードコード)。
- `merge_prices.py` は `prices.csv` に `code` (任意の形式、4桁ゼロ埋め) と `date` カラムを期待する。
- リンター、フォーマッター、型チェッカー、CI、pre-commit はなし。`pytest` のみ。