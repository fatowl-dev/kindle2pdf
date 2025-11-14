#!/usr/bin/env python3
"""
PNGファイルをJPGファイルに変換するスクリプト

使用例:
    python png_to_jpg.py /path/to/png/folder
    python png_to_jpg.py /Users/fatowl/Desktop/images --quality 90
    python png_to_jpg.py ./screenshots --output ./converted --delete-original
"""

import os
import sys
import argparse
import glob
import re
from PIL import Image


def natural_sort_key(text):
    """
    自然順序でソートするためのキー関数
    例: image_1.png, image_2.png, image_10.png の順序を正しく保つ
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', text)]


def find_png_files(input_folder, pattern="*.png"):
    """
    指定されたフォルダからPNGファイルを検索
    
    Args:
        input_folder (str): 検索対象のフォルダパス
        pattern (str): ファイル名パターン（デフォルト: "*.png"）
    
    Returns:
        list: ソートされたPNGファイルパスのリスト
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"入力フォルダが見つかりません: {input_folder}")
    
    if not os.path.isdir(input_folder):
        raise NotADirectoryError(f"指定されたパスはフォルダではありません: {input_folder}")
    
    # パターンに基づいてファイルを検索
    search_pattern = os.path.join(input_folder, pattern)
    png_files = glob.glob(search_pattern)
    
    # PNGファイルのみをフィルタリング
    png_files = [f for f in png_files if f.lower().endswith('.png')]
    
    if not png_files:
        raise FileNotFoundError(f"PNGファイルが見つかりません: {search_pattern}")
    
    # 自然順序でソート
    png_files.sort(key=natural_sort_key)
    
    return png_files


def convert_png_to_jpg(png_file, output_folder=None, quality=95, delete_original=False):
    """
    PNGファイルをJPGファイルに変換
    
    Args:
        png_file (str): PNGファイルのパス
        output_folder (str): 出力フォルダ（Noneの場合は元のフォルダと同じ）
        quality (int): JPEG品質（1-100、デフォルト: 95）
        delete_original (bool): 元のPNGファイルを削除するか（デフォルト: False）
    
    Returns:
        str: 変換後のJPGファイルパス、失敗時はNone
    """
    try:
        # 画像を開く
        img = Image.open(png_file)
        
        # RGBAモードの場合はRGBに変換（JPGはアルファチャンネルをサポートしない）
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
        
        # 出力ファイルパスを決定
        if output_folder:
            # 出力フォルダが指定されている場合
            os.makedirs(output_folder, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(png_file))[0]
            jpg_file = os.path.join(output_folder, f"{base_name}.jpg")
        else:
            # 元のフォルダと同じ場所に保存
            jpg_file = os.path.splitext(png_file)[0] + ".jpg"
        
        # JPGとして保存
        img.save(jpg_file, 'JPEG', quality=quality, optimize=True)
        
        # 元のファイルを削除（オプション）
        if delete_original:
            os.remove(png_file)
        
        img.close()
        return jpg_file
        
    except Exception as e:
        print(f"✗ エラー: {png_file} の変換に失敗しました: {e}")
        return None


def convert_folder(input_folder, output_folder=None, quality=95, delete_original=False):
    """
    フォルダ内の全PNGファイルをJPGに変換
    
    Args:
        input_folder (str): 入力フォルダパス
        output_folder (str): 出力フォルダ（Noneの場合は入力フォルダと同じ）
        quality (int): JPEG品質（1-100）
        delete_original (bool): 元のPNGファイルを削除するか
    """
    # PNGファイルを検索
    png_files = find_png_files(input_folder)
    
    print(f"見つかったPNGファイル数: {len(png_files)}")
    if output_folder:
        print(f"出力フォルダ: {output_folder}")
    else:
        print(f"出力先: 入力フォルダと同じ場所")
    print(f"品質設定: {quality}")
    print(f"元のファイル削除: {'有効' if delete_original else '無効'}")
    print("=" * 60)
    
    converted_count = 0
    failed_count = 0
    total_size_saved = 0
    
    for i, png_file in enumerate(png_files, 1):
        print(f"処理中 ({i}/{len(png_files)}): {os.path.basename(png_file)}")
        
        # 元のファイルサイズを記録
        original_size = os.path.getsize(png_file)
        
        # 変換実行
        jpg_file = convert_png_to_jpg(
            png_file=png_file,
            output_folder=output_folder,
            quality=quality,
            delete_original=delete_original
        )
        
        if jpg_file:
            converted_count += 1
            # ファイルサイズを比較
            jpg_size = os.path.getsize(jpg_file)
            size_diff = original_size - jpg_size
            total_size_saved += size_diff
            
            if size_diff > 0:
                print(f"  ✓ 変換完了: {os.path.basename(jpg_file)} "
                      f"({original_size:,} bytes → {jpg_size:,} bytes, "
                      f"-{size_diff:,} bytes)")
            else:
                print(f"  ✓ 変換完了: {os.path.basename(jpg_file)} "
                      f"({original_size:,} bytes → {jpg_size:,} bytes)")
        else:
            failed_count += 1
    
    print("\n" + "=" * 60)
    print("変換結果")
    print("=" * 60)
    print(f"成功: {converted_count}個")
    if failed_count > 0:
        print(f"失敗: {failed_count}個")
    if total_size_saved > 0:
        print(f"合計サイズ削減: {total_size_saved:,} bytes ({total_size_saved / 1024 / 1024:.2f} MB)")
    print("=" * 60)


def parse_arguments():
    """
    コマンドライン引数を解析
    """
    parser = argparse.ArgumentParser(
        description="PNGファイルをJPGファイルに変換するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python png_to_jpg.py /path/to/png/folder
  python png_to_jpg.py ./screenshots --output ./converted --quality 90
  python png_to_jpg.py /Users/fatowl/Desktop/images --delete-original
  python png_to_jpg.py ./images --output ./jpg --quality 85 --delete-original
        """
    )
    
    parser.add_argument(
        "input_folder",
        type=str,
        help="PNGファイルが格納されているフォルダパス"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="出力フォルダパス（指定しない場合は入力フォルダと同じ場所）"
    )
    
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        choices=range(1, 101),
        metavar="1-100",
        help="JPEG品質（1-100、デフォルト: 95）"
    )
    
    parser.add_argument(
        "-d", "--delete-original",
        action="store_true",
        help="変換後に元のPNGファイルを削除する"
    )
    
    parser.add_argument(
        "-p", "--pattern",
        type=str,
        default="*.png",
        help="ファイル名パターン（デフォルト: *.png）"
    )
    
    return parser.parse_args()


def main():
    """
    メイン処理
    """
    try:
        # コマンドライン引数を解析
        args = parse_arguments()
        
        print("=" * 60)
        print("PNG → JPG 変換ツール")
        print("=" * 60)
        print(f"入力フォルダ: {args.input_folder}")
        if args.output:
            print(f"出力フォルダ: {args.output}")
        print(f"ファイルパターン: {args.pattern}")
        print(f"品質設定: {args.quality}")
        print(f"元のファイル削除: {'有効' if args.delete_original else '無効'}")
        print("=" * 60)
        
        # 変換実行
        convert_folder(
            input_folder=args.input_folder,
            output_folder=args.output,
            quality=args.quality,
            delete_original=args.delete_original
        )
        
        print("\n✓ 変換が正常に完了しました！")
        
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

