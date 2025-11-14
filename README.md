# Kindless - Kindle スクリーンショット自動化ツール

Kindle本のスクリーンショットを自動で撮影し、PDFに変換するPythonツールです。

## 概要

このツールは以下の機能を提供します：

1. **kindless.py** - Kindleアプリのスクリーンショットを自動撮影
2. **remove_duplicate_images.py** - 重複画像を自動検出・削除
3. **png_to_jpg.py** - PNG画像をJPG画像に変換（ファイルサイズ削減）
4. **image_to_pdf.py** - 画像ファイル（PNG/JPG）をPDFに変換
5. **kindle2pdf.py** - 上記処理を統合したパイプラインスクリプト

## 必要な環境

- Python 3.6以上（**Python 3.13は非対応**）
- macOS / Windows / Linux対応
- Kindleアプリ（デスクトップ版）

### Python バージョンに関する注意

⚠️ **Python 3.13では動作しません**

このツールはPython 3.13では正常に動作しないことが確認されています。以下のバージョンでの使用を推奨します：

- **推奨**: Python 3.8 〜 3.12
- **最小要件**: Python 3.6以上
- **非対応**: Python 3.13以降

## インストール

1. リポジトリをクローンまたはダウンロード
2. 仮想環境を作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows
```

3. 必要なパッケージをインストール
```bash
# 方法1: requirements.txtを使用（推奨）
pip install -r requirements.txt

# 方法2: 個別にインストール
pip install pyautogui pillow scikit-image
```

## 設定

`config.json`ファイルで設定をカスタマイズできます：

```json
{
    "output_folder": "/Users/username/Desktop/KindleScreenshots",
    "book_title": "本のタイトル",
    "page_delay": 2,
    "num_pages": 100,
    "pdf_output_folder": "/Users/username/Desktop/PDFs",
    "pdf_filename": null,
    "similarity_threshold": 0.99,
    "jpg_quality": 95,
    "pages_per_pdf": 50
}
```

### 設定項目の説明

| 項目 | 説明 | デフォルト値 | 範囲・形式 |
|------|------|-------------|-----------|
| `output_folder` | スクリーンショットの保存先フォルダ | `~/Documents` | フォルダパス |
| `book_title` | 本のタイトル（サブフォルダ名として使用） | `"KindleBook"` | 文字列 |
| `page_delay` | ページめくり後の待機時間（秒） | `2` | 1-10 |
| `num_pages` | キャプチャするページ数 | `100` | 1-2000 |
| `pdf_output_folder` | PDF出力先フォルダ | `null`（カレントディレクトリ） | フォルダパス |
| `pdf_filename` | PDF出力ファイル名 | `null`（book_title.pdf） | ファイル名 |
| `similarity_threshold` | 重複画像判定の類似度閾値 | `0.99` | 0.0-1.0 |
| `jpg_quality` | JPG変換時の品質設定 | `95` | 1-100 |
| `pages_per_pdf` | 1つのPDFあたりのページ数（分割設定） | `null`（分割しない） | 正の整数 |

#### 画像一致度閾値について

`similarity_threshold`は以下の2つの用途で使用されます：

1. **スクリーンショット撮影時の自動終了判定**（`kindless.py`）
   - 前回のスクリーンショットと比較し、同じ画像が10回連続したら自動終了
   - 本の最後やページめくりが止まった場合に自動停止

2. **重複画像削除時の判定**（`remove_duplicate_images.py`）
   - 同一ディレクトリ内の画像を比較し、重複を検出・削除

**推奨値**：
- **0.99（推奨）**: 非常に高精度。ほぼ同一の画像のみを重複と判定
- **0.95**: 高精度。わずかな違いがある画像も重複と判定
- **0.90**: 中精度。より多くの類似画像を重複と判定
- **0.85以下**: 低精度。異なる画像も重複と誤判定する可能性が高い

**注意**: 
- 値を下げすぎると、異なるページの画像も重複として削除される可能性があります
- スクリーンショット撮影時の自動終了機能では、0.99が推奨されます（本の最後を正確に検出するため）

#### JPG品質設定について

`jpg_quality`はPNG画像をJPGに変換する際の圧縮品質を設定します：

- **95（推奨）**: 高品質。ファイルサイズと品質のバランスが良い
- **85-90**: 中品質。ファイルサイズを抑えつつ、品質を維持
- **75-80**: 低品質。ファイルサイズを大幅に削減（画質は若干低下）
- **100**: 最高品質。ファイルサイズが大きくなる

**注意**: 値が高いほど品質は向上しますが、ファイルサイズも大きくなります。一般的には85-95の範囲が推奨されます。

#### PDF分割設定について

`pages_per_pdf`は、PDF変換時に指定ページ数ごとにPDFファイルを分割する機能です：

- **設定しない場合（`null`）**: すべての画像を1つのPDFファイルに変換します
- **設定した場合**: 指定したページ数ごとにPDFファイルを分割します
  - 例: `pages_per_pdf: 50` を設定し、150ページの画像を変換すると、`book_1.pdf`（50ページ）、`book_2.pdf`（50ページ）、`book_3.pdf`（50ページ）の3つのPDFが作成されます
  - 出力ファイル名は自動的に連番が追加されます（`<出力ファイル名>_1.pdf`, `<出力ファイル名>_2.pdf`など）

**使用例**:
- 大きな本を複数のPDFに分割して管理したい場合
- ファイルサイズを小さくして扱いやすくしたい場合
- 特定のページ範囲だけを共有したい場合

## 使用方法

### 統合パイプライン（推奨）

全ての処理を一度に実行する統合スクリプトが利用できます：

```bash
# 全ての処理を順番に実行（スクリーンショット → 重複削除 → PNG→JPG変換 → PDF変換）
python kindle2pdf.py

# ドライランモード（実際の処理は行わず、計画のみ表示）
python kindle2pdf.py --dry-run

# スクリーンショットをスキップして重複削除、PNG→JPG変換、PDF変換のみ実行
python kindle2pdf.py --skip-screenshots

# PNG→JPG変換をスキップ
python kindle2pdf.py --skip-png-to-jpg

# 重複削除をスキップ
python kindle2pdf.py --skip-duplicates

# PDF変換をスキップ（スクリーンショット、重複削除、PNG→JPG変換のみ実行）
python kindle2pdf.py --skip-pdf

# カスタム設定ファイルを使用
python kindle2pdf.py --config my_config.json
```

#### 統合パイプラインの特徴

- **自動化**: 4つの処理を順番に自動実行
  1. Kindleスクリーンショット撮影（PNG形式）
     - 画像比較による自動終了機能（10回連続で同じ画像が続いたら終了）
     - `config.json`の`similarity_threshold`を自動的に`kindless.py`に渡す
  2. 重複画像削除
     - `config.json`の`similarity_threshold`を使用
  3. PNG → JPG変換（`<book_title>_jpg`フォルダに保存、元のPNGファイルは保持）
     - `config.json`の`jpg_quality`を使用
  4. PDF変換（JPGフォルダが存在する場合はJPGフォルダから、存在しない場合は元のスクリーンショットフォルダから）
- **設定ファイル連携**: `config.json`から全ての設定を自動読み込み
  - `similarity_threshold`: スクリーンショット撮影と重複削除の両方で使用
  - `jpg_quality`: PNG → JPG変換時の品質設定
  - `pages_per_pdf`: PDF分割設定（指定ページ数ごとにPDFを分割）
  - その他の設定（`book_title`, `page_delay`, `num_pages`など）も自動適用
- **エラーハンドリング**: 各ステップでのエラー検出と適切な停止
- **進捗表示**: 各ステップの実行状況を詳細表示
- **柔軟性**: 必要に応じて特定のステップをスキップ可能
  - `--skip-screenshots`: スクリーンショット撮影をスキップ
  - `--skip-png-to-jpg`: PNG → JPG変換をスキップ
  - `--skip-duplicates`: 重複画像削除をスキップ
  - `--skip-pdf`: PDF変換をスキップ
- **ドライラン**: 実際の処理前に実行計画を確認（`--dry-run`）
- **JPGフォルダ管理**: PNG → JPG変換時に`<book_title>_jpg`フォルダを自動作成し、元のPNGファイルは保持

### 個別スクリプトの使用方法

#### 1. スクリーンショット撮影

```bash
python kindless.py -t "本のタイトル" -p 100 -d 2
```

オプション：
- `-t, --title`: 本のタイトル（保存フォルダ名）
- `-p, --pages`: キャプチャするページ数
- `-d, --delay`: ページめくり後の待機時間（秒）
- `-o, --output`: 出力フォルダのパス
- `-c, --config`: 設定ファイルのパス
- `-s, --similarity`: 画像類似度の閾値（0.0-1.0、デフォルト: 0.99）

使用例：
```bash
# 基本的な使用方法
python kindless.py -t "マイブック" -p 100 -d 3

# 類似度95%で判定（より緩い判定）
python kindless.py -t "マイブック" -s 0.95

# 設定ファイルを使用
python kindless.py --config config.json

# 類似度とその他のオプションを組み合わせ
python kindless.py -t "小説" --pages 50 --delay 1 --similarity 0.98
```

##### スクリーンショット撮影の特徴

- **自動終了機能**: スクリーンショットを1つ取るたびに前回の画像と比較し、10回連続で同じ画像が続いたら自動終了
- **SSIMベースの画像比較**: `remove_duplicate_images.py`と同じSSIM（構造的類似性指数）を使用した高精度な画像比較
- **類似度閾値の設定**: `--similarity`オプションまたは`config.json`の`similarity_threshold`で類似度を調整可能
- **OS別のページめくり**: macOS/Windows/Linuxで最適なページめくり方法を自動選択
- **フェイルセーフ機能**: マウスを画面左上角に移動すると処理が停止

#### 2. PNG → JPG変換

```bash
python png_to_jpg.py /path/to/png/folder
```

オプション：
- `input_folder`: PNGファイルが格納されているフォルダ（位置引数）
- `-o, --output`: 出力フォルダパス（指定しない場合は入力フォルダと同じ場所）
- `-q, --quality`: JPEG品質（1-100、デフォルト: 95）
- `-d, --delete-original`: 変換後に元のPNGファイルを削除
- `-p, --pattern`: ファイル名パターン（デフォルト: *.png）

使用例：
```bash
# 基本的な使用方法（同一ディレクトリにJPGを保存）
python png_to_jpg.py ./screenshots

# 出力フォルダを指定
python png_to_jpg.py ./screenshots --output ./converted

# 品質を指定して変換後、元のPNGを削除
python png_to_jpg.py ./screenshots --quality 90 --delete-original
```

#### 3. PDF変換

```bash
python image_to_pdf.py -i /path/to/images -o output.pdf
```

オプション：
- `-i, --input`: 画像ファイル（PNG/JPG）が格納されているフォルダ
- `-o, --output`: 出力PDFファイルのパス
- `-p, --pattern`: ファイル名パターン（デフォルト: *.pngと*.jpgの両方を検索）
- `-q, --quality`: PDF品質（1-100、デフォルト: 95）
- `--pages-per-pdf`: 1つのPDFあたりのページ数（指定すると指定ページ数ごとにPDFを分割）
- `-y, --yes`: 確認プロンプトをスキップ

**注意**: `image_to_pdf.py`はPNGとJPGの両方の画像形式に対応しています。パターンが指定されていない場合、フォルダ内のPNGとJPGファイルの両方を自動的に検索します。

**PDF分割機能**:
```bash
# 50ページごとにPDFを分割
python image_to_pdf.py -i ./images -o book.pdf --pages-per-pdf 50

# 100ページごとにPDFを分割
python image_to_pdf.py -i ./images -o output.pdf --pages-per-pdf 100
```

分割時は、出力ファイル名に自動的に連番が追加されます：
- `book.pdf` → `book_1.pdf`, `book_2.pdf`, `book_3.pdf` など

#### 4. 重複画像削除

```bash
python remove_duplicate_images.py --dry-run
```

基本的な使用方法：
```bash
# 現在のディレクトリで重複画像を検出（削除はしない）
python remove_duplicate_images.py --dry-run

# 指定ディレクトリで重複画像を削除
python remove_duplicate_images.py -d /path/to/images

# 類似度90%で重複を判定
python remove_duplicate_images.py -t 0.9

# ディレクトリと類似度を両方指定
python remove_duplicate_images.py -d /path/to/images -t 0.95

# バックアップなしで削除
python remove_duplicate_images.py --no-backup
```

オプション：
- `directory`: 対象ディレクトリのパス（位置引数）
- `-d, --directory`: 対象ディレクトリのパス（オプション引数）
- `-t, --threshold`: 類似度の閾値（0.0-1.0、デフォルト: 0.99）
- `--dry-run`: 実際には削除せず、削除対象のみ表示
- `--no-backup`: 削除前のバックアップを作成しない

##### 重複画像削除の特徴

- **高精度判定**: SSIM（構造的類似性指数）による99%精度の重複判定
- **安全機能**: 削除前の自動バックアップ（`backup_duplicates_YYYYMMDD_HHMMSS`フォルダ）
- **ドライラン機能**: `--dry-run`で削除対象を事前確認
- **進捗表示**: 大量ファイル処理時の進捗状況表示
- **RGBA対応**: 透明度付き画像も適切に処理

## ⚠️ 重要な注意点

### 権限設定（macOS）

macOSでは以下の権限設定が必要です：

1. **システム環境設定** → **セキュリティとプライバシー** → **プライバシー**
2. **「画面録画」** でPythonまたはターミナルを許可
3. **「アクセシビリティ」** でPythonまたはターミナルを許可
4. 設定変更後、ターミナルを再起動

### 権限設定（Windows）

- 管理者権限でコマンドプロンプトまたはPowerShellを実行
- ウイルス対策ソフトがpyautoguiをブロックしていないか確認
- Windows Defenderの例外設定を確認

### 使用上の注意

1. **フェイルセーフ機能**: マウスを画面左上角に移動すると処理が停止します
2. **Kindleアプリの準備**: 撮影開始前にKindleアプリを開き、最初のページを表示してください
3. **画面の妨害禁止**: 撮影中は他のアプリケーションを操作しないでください
4. **ページめくり方法**: 
   - macOS: スペースキー → 右矢印キー → 画面右側クリック
   - Windows: 右矢印キー → スペースキー → 画面右側クリック → PageDownキー
5. **自動終了機能**: スクリーンショットを1つ取るたびに前回の画像と比較し、10回連続で同じ画像が続いたら自動終了します（本の最後を検出）
6. **連続エラー**: 3回連続でエラーが発生すると自動停止します
7. **無限ループ防止**: 2000ページを超えると強制終了します
8. **類似度閾値の設定**: `config.json`の`similarity_threshold`を調整することで、自動終了の感度を変更できます（デフォルト: 0.99）

### パス指定時の注意（重要）

⚠️ **チルダ（~）の使用について**

コマンドライン引数でパスを指定する際は、以下の点にご注意ください：

```bash
# ❌ 間違った例（チルダが正しく展開されない場合があります）
python image_to_pdf.py --input ~/Documents/BookTitle --output ~/Documents/BookTitle.pdf

# ✅ 正しい例（絶対パスを使用）
python image_to_pdf.py --input /Users/username/Documents/BookTitle --output /Users/username/Documents/BookTitle.pdf

# ✅ または相対パスを使用
python image_to_pdf.py --input ../Documents/BookTitle --output ../Documents/BookTitle.pdf
```

**問題の詳細:**
- チルダ（`~`）がPythonスクリプト内で正しく展開されない場合、ファイルが予期しない場所に保存される可能性があります
- 例：`~/Documents/file.pdf` → `./~/Documents/file.pdf`（現在のディレクトリ下に`~`フォルダが作成される）

**推奨される対処法:**
1. **絶対パス**を使用する（最も確実）
2. **相対パス**を使用する
3. 設定ファイル（`config.json`）で事前にパスを設定する

### ファイル形式とサイズ

- スクリーンショット: PNG形式（`<book_title>`フォルダに保存）
- 中間形式: JPG形式（`<book_title>_jpg`フォルダに保存、元のPNGファイルは保持）
- 出力PDF: RGB形式（アルファチャンネルは白背景に変換）
- ファイル名: `page_0001.png` → `page_0001.jpg` → PDFに統合

**パイプラインの処理フロー:**
1. PNGスクリーンショット撮影（`<book_title>`フォルダ）
2. 重複PNG画像の削除
3. PNG → JPG変換（`<book_title>_jpg`フォルダに保存、元のPNGファイルは保持）
4. PDF変換（`<book_title>_jpg`フォルダが存在する場合はJPGフォルダから、存在しない場合は元のスクリーンショットフォルダから）

**フォルダ構造の例:**
```
output_folder/
├── 本のタイトル/          # スクリーンショット（PNG）
│   ├── page_0001.png
│   ├── page_0002.png
│   └── ...
└── 本のタイトル_jpg/      # JPG変換後（元のPNGは保持）
    ├── page_0001.jpg
    ├── page_0002.jpg
    └── ...
```

## トラブルシューティング

### よくあるエラー

1. **Python 3.13互換性エラー**: Python 3.12以下のバージョンを使用してください
2. **権限エラー**: 上記の権限設定を確認してください
3. **ページめくり失敗**: Kindleアプリがアクティブか確認してください
4. **ファイル保存エラー**: 出力フォルダの書き込み権限を確認してください
5. **PDF変換エラー**: PNGファイルが破損していないか確認してください
6. **重複画像削除エラー**: scikit-imageライブラリがインストールされているか確認してください

### Python バージョン確認方法

現在のPythonバージョンを確認するには：

```bash
python --version
# または
python3 --version
```

Python 3.13を使用している場合は、以下の方法で適切なバージョンをインストールしてください：

```bash
# pyenvを使用する場合（推奨）
pyenv install 3.12.0
pyenv local 3.12.0

# または仮想環境で特定のバージョンを指定
python3.12 -m venv venv
```

### デバッグ情報

エラーが発生した場合、以下の情報が表示されます：
- エラータイプ
- ファイルパス
- ファイルサイズ
- OS情報

## ライセンス

このプロジェクトは個人利用を目的としています。商用利用や著作権で保護されたコンテンツの無断複製は禁止されています。

## 免責事項

- このツールの使用は自己責任で行ってください
- 著作権法を遵守して使用してください
- 商用利用や配布は著作権者の許可を得てください
- 開発者は本ツールの使用による一切の損害について責任を負いません
