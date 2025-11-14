#!/usr/bin/env python3
"""
連番画像ファイル（PNG/JPG）をPDFに変換するスクリプト

使用例:
    python image_to_pdf.py -i /path/to/image/folder -o output.pdf
    python image_to_pdf.py -i /Users/fatowl/Desktop/KindleScreenshots/MyKindleBook -o book.pdf
    python image_to_pdf.py --input ./images --output combined.pdf --pattern "page_*.png"
    python image_to_pdf.py --input ./images --output combined.pdf --pattern "*.jpg"
    python image_to_pdf.py -i ./images -o book.pdf --pages-per-pdf 50  # 50ページごとに分割
"""

import os
import sys
import argparse
import glob
import re
from PIL import Image
import json

def natural_sort_key(text):
    """
    自然順序でソートするためのキー関数
    例: page_1.png, page_2.png, page_10.png の順序を正しく保つ
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', text)]

def find_image_files(input_folder, pattern=None):
    """
    指定されたフォルダから連番画像ファイル（PNG/JPG）を検索
    
    Args:
        input_folder (str): 検索対象のフォルダパス
        pattern (str): ファイル名パターン（Noneの場合は*.pngと*.jpgを検索）
    
    Returns:
        list: ソートされた画像ファイルパスのリスト
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"入力フォルダが見つかりません: {input_folder}")
    
    if not os.path.isdir(input_folder):
        raise NotADirectoryError(f"指定されたパスはフォルダではありません: {input_folder}")
    
    # パターンが指定されていない場合は、PNGとJPGの両方を検索
    if pattern is None:
        patterns = ["*.png", "*.jpg", "*.jpeg"]
    else:
        patterns = [pattern]
    
    image_files = []
    for pat in patterns:
        search_pattern = os.path.join(input_folder, pat)
        found_files = glob.glob(search_pattern)
        image_files.extend(found_files)
    
    # PNG/JPG/JPEGファイルのみをフィルタリング
    image_files = [f for f in image_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        raise FileNotFoundError(f"画像ファイル（PNG/JPG）が見つかりません: {input_folder}")
    
    # 自然順序でソート
    image_files.sort(key=natural_sort_key)
    
    print(f"見つかった画像ファイル数: {len(image_files)}")
    print(f"最初のファイル: {os.path.basename(image_files[0])}")
    print(f"最後のファイル: {os.path.basename(image_files[-1])}")
    
    return image_files

def convert_images_to_pdf(image_files, output_pdf, quality=95, optimize=True, pages_per_pdf=None):
    """
    画像ファイルリスト（PNG/JPG）をPDFに変換
    
    Args:
        image_files (list): 画像ファイルパスのリスト（PNG/JPG）
        output_pdf (str): 出力PDFファイルパス（分割時はベース名として使用）
        quality (int): JPEG品質（1-100、デフォルト: 95）
        optimize (bool): PDF最適化を行うか（デフォルト: True）
        pages_per_pdf (int): 1つのPDFあたりのページ数（Noneの場合は全ページを1つのPDFに）
    """
    if not image_files:
        raise ValueError("変換する画像ファイルがありません")
    
    print(f"PDF変換を開始します...")
    print(f"出力ファイル: {output_pdf}")
    if pages_per_pdf:
        print(f"分割設定: {pages_per_pdf}ページごとに分割")
    print(f"品質設定: {quality}")
    print(f"最適化: {'有効' if optimize else '無効'}")
    
    images = []
    failed_files = []
    
    for i, image_file in enumerate(image_files, 1):
        try:
            print(f"処理中 ({i}/{len(image_files)}): {os.path.basename(image_file)}")
            
            # 画像を開く
            img = Image.open(image_file)
            
            # RGBAモードの場合はRGBに変換（PDFはアルファチャンネルをサポートしない）
            if img.mode in ('RGBA', 'LA'):
                # 白い背景を作成
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # アルファチャンネルをマスクとして使用
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
            
        except Exception as e:
            print(f"✗ エラー: {image_file} の読み込みに失敗しました: {e}")
            failed_files.append(image_file)
            continue
    
    if not images:
        raise RuntimeError("変換可能な画像がありませんでした")
    
    if failed_files:
        print(f"\n警告: {len(failed_files)}個のファイルの読み込みに失敗しました:")
        for failed_file in failed_files:
            print(f"  - {os.path.basename(failed_file)}")
    
    # 出力ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname(output_pdf)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 出力ファイル名のベース名と拡張子を取得
    base_name, ext = os.path.splitext(output_pdf)
    if not ext:
        ext = '.pdf'
    
    try:
        # ページ数ごとに分割する場合
        if pages_per_pdf and pages_per_pdf > 0:
            total_pages = len(images)
            num_pdfs = (total_pages + pages_per_pdf - 1) // pages_per_pdf  # 切り上げ
            
            print(f"\n{total_pages}ページを{num_pdfs}個のPDFファイルに分割します...")
            
            created_files = []
            for pdf_num in range(num_pdfs):
                start_idx = pdf_num * pages_per_pdf
                end_idx = min(start_idx + pages_per_pdf, total_pages)
                chunk_images = images[start_idx:end_idx]
                
                # 出力ファイル名を生成（連番を追加）
                if num_pdfs > 1:
                    chunk_output_pdf = f"{base_name}_{pdf_num + 1}{ext}"
                else:
                    chunk_output_pdf = output_pdf
                
                print(f"\nPDF {pdf_num + 1}/{num_pdfs} を作成中...")
                print(f"  ページ範囲: {start_idx + 1} - {end_idx}")
                print(f"  出力ファイル: {chunk_output_pdf}")
                
                # PDFとして保存
                if len(chunk_images) > 0:
                    chunk_images[0].save(
                        chunk_output_pdf,
                        save_all=True,
                        append_images=chunk_images[1:] if len(chunk_images) > 1 else [],
                        format='PDF',
                        optimize=optimize,
                        quality=quality
                    )
                    
                    # ファイルサイズを確認
                    if os.path.exists(chunk_output_pdf):
                        file_size = os.path.getsize(chunk_output_pdf)
                        print(f"  ✓ PDF作成完了!")
                        print(f"    サイズ: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                        print(f"    ページ数: {len(chunk_images)}")
                        created_files.append(chunk_output_pdf)
                    else:
                        raise RuntimeError(f"PDFファイルが作成されませんでした: {chunk_output_pdf}")
            
            print(f"\n✓ 全{num_pdfs}個のPDFファイルの作成が完了しました！")
            print(f"  作成されたファイル:")
            for created_file in created_files:
                print(f"    - {created_file}")
        
        else:
            # 分割しない場合（従来の動作）
            print(f"\nPDFファイルを作成中...")
            
            # 最初の画像を使ってPDFを作成し、残りの画像を追加
            images[0].save(
                output_pdf,
                save_all=True,
                append_images=images[1:],
                format='PDF',
                optimize=optimize,
                quality=quality
            )
            
            # ファイルサイズを確認
            if os.path.exists(output_pdf):
                file_size = os.path.getsize(output_pdf)
                print(f"✓ PDF作成完了!")
                print(f"  ファイル: {output_pdf}")
                print(f"  サイズ: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                print(f"  ページ数: {len(images)}")
            else:
                raise RuntimeError("PDFファイルが作成されませんでした")
            
    except Exception as e:
        raise RuntimeError(f"PDF作成に失敗しました: {e}")
    
    finally:
        # メモリを解放
        for img in images:
            img.close()

def load_config_for_pdf(config_file="config.json"):
    """
    設定ファイルからPDF変換用の設定を読み込む
    
    Args:
        config_file (str): 設定ファイルのパス
    
    Returns:
        dict: 設定辞書
    """
    default_config = {
        "output_folder": "/Users/fatowl/Desktop/KindleScreenshots",
        "book_title": "MyKindleBook",
        "pdf_output_folder": None,  # None の場合は入力フォルダと同じ場所
        "pdf_filename": None        # None の場合は book_title.pdf を使用
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                print(f"設定ファイル '{config_file}' を読み込みました")
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗: {e}")
    
    return default_config

def parse_arguments():
    """
    コマンドライン引数を解析
    """
    parser = argparse.ArgumentParser(
        description="連番画像ファイル（PNG/JPG）をPDFに変換するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python image_to_pdf.py -i /path/to/image/folder -o output.pdf
  python image_to_pdf.py -i ./screenshots -o book.pdf --pattern "page_*.png"
  python image_to_pdf.py -i ./screenshots -o book.pdf --pattern "*.jpg"
  python image_to_pdf.py --config config.json -y  # 設定ファイルから自動設定（確認なし）
  python image_to_pdf.py -i /Users/fatowl/Desktop/KindleScreenshots/MyKindleBook -o MyBook.pdf -y
  python image_to_pdf.py -i ./images -o book.pdf --pages-per-pdf 50  # 50ページごとに分割
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        help="画像ファイル（PNG/JPG）が格納されているフォルダパス"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="出力PDFファイルのパス"
    )
    
    parser.add_argument(
        "-p", "--pattern",
        type=str,
        default=None,
        help="ファイル名パターン（デフォルト: *.pngと*.jpgの両方を検索）"
    )
    
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        choices=range(1, 101),
        metavar="1-100",
        help="PDF品質（1-100、デフォルト: 95）"
    )
    
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="PDF最適化を無効にする"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.json",
        help="設定ファイルのパス（デフォルト: config.json）"
    )
    
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="確認プロンプトをスキップして自動実行"
    )
    
    parser.add_argument(
        "--pages-per-pdf",
        type=int,
        default=None,
        metavar="N",
        help="1つのPDFあたりのページ数（指定すると指定ページ数ごとにPDFを分割）"
    )
    
    return parser.parse_args()

def main():
    """
    メイン処理
    """
    try:
        # コマンドライン引数を解析
        args = parse_arguments()
        
        # 設定ファイルを読み込み
        config = load_config_for_pdf(args.config)
        
        # 入力フォルダの決定
        if args.input:
            input_folder = args.input
        else:
            # 設定ファイルから自動設定
            input_folder = os.path.join(config["output_folder"], config["book_title"])
            print(f"設定ファイルから入力フォルダを自動設定: {input_folder}")
        
        # 出力ファイルの決定
        if args.output:
            output_pdf = args.output
        else:
            # 設定ファイルからPDF出力設定を取得
            pdf_output_folder = config.get("pdf_output_folder")
            pdf_filename = config.get("pdf_filename")
            book_title = config.get("book_title", "converted_book")
            
            # ファイル名の決定
            if pdf_filename:
                filename = pdf_filename
            else:
                filename = f"{book_title}.pdf"
            
            # 出力フォルダの決定
            if pdf_output_folder:
                output_pdf = os.path.join(pdf_output_folder, filename)
                print(f"PDF出力フォルダを設定ファイルから取得: {pdf_output_folder}")
            else:
                # PDF出力フォルダが指定されていない場合は、入力フォルダと同じ場所
                output_pdf = filename
                print(f"PDF出力フォルダが未指定のため、カレントディレクトリに出力")
            
            print(f"出力ファイル名を自動設定: {output_pdf}")
        
        print("=" * 60)
        print("画像 → PDF 変換ツール（PNG/JPG対応）")
        print("=" * 60)
        print(f"入力フォルダ: {input_folder}")
        print(f"出力ファイル: {output_pdf}")
        print(f"ファイルパターン: {args.pattern if args.pattern else '*.png, *.jpg, *.jpeg'}")
        print(f"品質設定: {args.quality}")
        print(f"最適化: {'無効' if args.no_optimize else '有効'}")
        if args.pages_per_pdf:
            print(f"分割設定: {args.pages_per_pdf}ページごとに分割")
        print("=" * 60)
        
        # 画像ファイルを検索（PNG/JPG対応）
        image_files = find_image_files(input_folder, args.pattern)
        
        # 確認プロンプト（--yesオプションでスキップ可能）
        print(f"\n{len(image_files)}個の画像ファイルをPDFに変換します。")
        if not args.yes:
            response = input("続行しますか？ (y/N): ").strip().lower()
            if response not in ['y', 'yes', 'はい']:
                print("変換をキャンセルしました。")
                return
        else:
            print("自動実行モードで続行します。")
        
        # PDF変換を実行
        convert_images_to_pdf(
            image_files=image_files,
            output_pdf=output_pdf,
            quality=args.quality,
            optimize=not args.no_optimize,
            pages_per_pdf=args.pages_per_pdf
        )
        
        print("\n" + "=" * 60)
        print("✓ 変換が正常に完了しました！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("✗ ユーザーによって処理が中断されました。")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ エラーが発生しました: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
