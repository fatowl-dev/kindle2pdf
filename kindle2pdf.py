#!/usr/bin/env python3
"""
Kindle → PDF 変換パイプライン

このスクリプトは以下の処理を順番に実行します：
1. Kindleスクリーンショットの自動撮影
2. 重複画像の削除
3. PNG画像のJPG変換（元のPNGファイルは削除）
4. JPG画像のPDF変換

使用例:
    python kindle2pdf.py
    python kindle2pdf.py --config custom_config.json
    python kindle2pdf.py --skip-screenshots  # スクリーンショットをスキップ
    python kindle2pdf.py --skip-png-to-jpg   # PNG → JPG変換をスキップ
    python kindle2pdf.py --skip-duplicates   # 重複削除をスキップ
    python kindle2pdf.py --skip-pdf          # PDF変換をスキップ
    python kindle2pdf.py --dry-run          # 実際の処理は行わず、計画のみ表示
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional


class KindleToPdfPipeline:
    def __init__(self, config_file: str = "config.json"):
        """
        パイプライン初期化
        
        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.script_dir = Path(__file__).parent
        
        # 各スクリプトのパス
        self.kindless_script = self.script_dir / "kindless.py"
        self.png_to_jpg_script = self.script_dir / "png_to_jpg.py"
        self.duplicate_remover_script = self.script_dir / "remove_duplicate_images.py"
        self.pdf_converter_script = self.script_dir / "image_to_pdf.py"
        
        # 処理対象フォルダ
        self.screenshots_folder = Path(self.config["output_folder"]) / self.config["book_title"]
        
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✓ 設定ファイルを読み込みました: {self.config_file}")
                return config
        except FileNotFoundError:
            print(f"✗ エラー: 設定ファイルが見つかりません: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ エラー: 設定ファイルの形式が正しくありません: {e}")
            sys.exit(1)
    
    def check_dependencies(self) -> bool:
        """必要なスクリプトファイルの存在確認"""
        scripts = [
            ("kindless.py", self.kindless_script),
            ("png_to_jpg.py", self.png_to_jpg_script),
            ("remove_duplicate_images.py", self.duplicate_remover_script),
            ("image_to_pdf.py", self.pdf_converter_script)
        ]
        
        missing_scripts = []
        for name, path in scripts:
            if not path.exists():
                missing_scripts.append(name)
        
        if missing_scripts:
            print(f"✗ エラー: 以下のスクリプトが見つかりません:")
            for script in missing_scripts:
                print(f"  - {script}")
            return False
        
        print("✓ 必要なスクリプトファイルを確認しました")
        return True
    
    def print_pipeline_info(self, skip_screenshots: bool, skip_png_to_jpg: bool, skip_duplicates: bool, skip_pdf: bool, dry_run: bool):
        """パイプライン実行情報を表示"""
        print("=" * 70)
        print("Kindle → PDF 変換パイプライン")
        print("=" * 70)
        print(f"本のタイトル: {self.config['book_title']}")
        print(f"ページ数: {self.config['num_pages']}")
        print(f"ページ間隔: {self.config['page_delay']}秒")
        print(f"スクリーンショット保存先: {self.config['output_folder']}")
        if not skip_pdf:
            print(f"PDF出力先: {self.config.get('pdf_output_folder', 'カレントディレクトリ')}")
            pages_per_pdf = self.config.get('pages_per_pdf')
            if pages_per_pdf:
                print(f"PDF分割設定: {pages_per_pdf}ページごとに分割")
        print(f"画像一致度閾値: {self.config.get('similarity_threshold', 0.99)}")
        if not skip_png_to_jpg:
            print(f"JPG品質: {self.config.get('jpg_quality', 95)}")
        print("-" * 70)
        
        steps = []
        if not skip_screenshots:
            steps.append("1. Kindleスクリーンショット撮影")
        if not skip_duplicates:
            steps.append(f"{len(steps)+1}. 重複画像削除")
        if not skip_png_to_jpg:
            steps.append(f"{len(steps)+1}. PNG → JPG変換")
        if not skip_pdf:
            steps.append(f"{len(steps)+1}. PDF変換")
        
        if dry_run:
            print("【ドライランモード】実際の処理は行いません")
        
        print("実行予定の処理:")
        for step in steps:
            print(f"  {step}")
        print("=" * 70)
    
    def run_screenshot_capture(self, dry_run: bool = False) -> bool:
        """
        Kindleスクリーンショット撮影を実行
        
        Args:
            dry_run: ドライランモード
            
        Returns:
            成功した場合True
        """
        print("\n" + "=" * 50)
        print("ステップ 1: Kindleスクリーンショット撮影")
        print("=" * 50)
        
        # 設定ファイルから類似度閾値を取得（デフォルト: 0.99）
        similarity_threshold = self.config.get("similarity_threshold", 0.99)
        
        # kindless.pyを実行するコマンドを構築
        cmd = [
            sys.executable, str(self.kindless_script),
            "--config", self.config_file,
            "--title", self.config["book_title"],
            "--pages", str(self.config["num_pages"]),
            "--delay", str(self.config["page_delay"]),
            "--output", self.config["output_folder"],
            "--similarity", str(similarity_threshold)
        ]
        
        if dry_run:
            print("【ドライラン】スクリーンショット撮影をシミュレート")
            print(f"  実行コマンド: {' '.join(cmd)}")
            print(f"  類似度閾値: {similarity_threshold:.1%}")
            return True
        
        try:
            
            print(f"実行コマンド: {' '.join(cmd)}")
            print(f"類似度閾値: {similarity_threshold:.1%}")
            print("注意: Kindleアプリを開いて最初のページを表示してください")
            
            result = subprocess.run(cmd, check=True, capture_output=False)
            
            if result.returncode == 0:
                print("✓ スクリーンショット撮影が完了しました")
                return True
            else:
                print(f"✗ スクリーンショット撮影が失敗しました (終了コード: {result.returncode})")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ スクリーンショット撮影でエラーが発生しました: {e}")
            return False
        except KeyboardInterrupt:
            print("✗ ユーザーによって中断されました")
            return False
    
    def run_png_to_jpg_conversion(self, dry_run: bool = False) -> bool:
        """
        PNG → JPG変換を実行
        
        Args:
            dry_run: ドライランモード
            
        Returns:
            成功した場合True
        """
        print("\n" + "=" * 50)
        print("ステップ 3: PNG → JPG変換")
        print("=" * 50)
        
        if not dry_run and not self.screenshots_folder.exists():
            print(f"✗ スクリーンショットフォルダが見つかりません: {self.screenshots_folder}")
            return False
        
        try:
            # JPG出力フォルダを作成（<book_title>_jpg）
            jpg_output_folder = Path(self.config["output_folder"]) / f"{self.config['book_title']}_jpg"
            
            # JPG品質を設定ファイルから取得（デフォルト: 95）
            jpg_quality = self.config.get("jpg_quality", 95)
            
            if dry_run:
                print("【ドライラン】PNG → JPG変換をシミュレート")
                print(f"  入力フォルダ: {self.screenshots_folder}")
                print(f"  出力フォルダ: {jpg_output_folder}")
                print(f"  JPG品質: {jpg_quality}")
                print(f"  元のファイル削除: 無効")
                return True
            
            # 出力フォルダを作成
            jpg_output_folder.mkdir(parents=True, exist_ok=True)
            print(f"出力フォルダ: {jpg_output_folder}")
            print(f"JPG品質: {jpg_quality}")
            
            # png_to_jpg.pyを実行（--outputオプションで出力フォルダを指定、--qualityで品質を指定、元のファイルは削除しない）
            cmd = [
                sys.executable, str(self.png_to_jpg_script),
                str(self.screenshots_folder),
                "--output", str(jpg_output_folder),
                "--quality", str(jpg_quality)
            ]
            
            print(f"実行コマンド: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=True, capture_output=False)
            
            if result.returncode == 0:
                print(f"✓ PNG → JPG変換が完了しました（出力先: {jpg_output_folder}）")
                return True
            else:
                print(f"✗ PNG → JPG変換が失敗しました (終了コード: {result.returncode})")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ PNG → JPG変換でエラーが発生しました: {e}")
            return False
        except KeyboardInterrupt:
            print("✗ ユーザーによって中断されました")
            return False
    
    def run_duplicate_removal(self, dry_run: bool = False) -> bool:
        """
        重複画像削除を実行
        
        Args:
            dry_run: ドライランモード
            
        Returns:
            成功した場合True
        """
        print("\n" + "=" * 50)
        print("ステップ 2: 重複画像削除")
        print("=" * 50)
        
        if not dry_run and not self.screenshots_folder.exists():
            print(f"✗ スクリーンショットフォルダが見つかりません: {self.screenshots_folder}")
            return False
        
        try:
            # remove_duplicate_images.pyを実行
            # 設定ファイルから類似度閾値を取得（デフォルト: 0.99）
            similarity_threshold = self.config.get("similarity_threshold", 0.99)
            
            cmd = [
                sys.executable, str(self.duplicate_remover_script),
                "--directory", str(self.screenshots_folder),
                "--threshold", str(similarity_threshold)
            ]
            
            if dry_run:
                print("【ドライラン】重複画像削除をシミュレート")
                print(f"実行コマンド: {' '.join(cmd + ['--dry-run'])}")
                return True
            else:
                cmd.append("--no-backup")  # バックアップなしで実行
            
            print(f"実行コマンド: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=True, capture_output=False)
            
            if result.returncode == 0:
                print("✓ 重複画像削除が完了しました")
                return True
            else:
                print(f"✗ 重複画像削除が失敗しました (終了コード: {result.returncode})")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ 重複画像削除でエラーが発生しました: {e}")
            return False
        except KeyboardInterrupt:
            print("✗ ユーザーによって中断されました")
            return False
    
    def run_pdf_conversion(self, dry_run: bool = False) -> bool:
        """
        PDF変換を実行
        
        Args:
            dry_run: ドライランモード
            
        Returns:
            成功した場合True
        """
        print("\n" + "=" * 50)
        print("ステップ 4: PDF変換")
        print("=" * 50)
        
        # JPGフォルダが存在する場合はそちらを優先
        jpg_output_folder = Path(self.config["output_folder"]) / f"{self.config['book_title']}_jpg"
        input_folder = jpg_output_folder if jpg_output_folder.exists() else self.screenshots_folder
        
        if not dry_run and not input_folder.exists():
            print(f"✗ 入力フォルダが見つかりません: {input_folder}")
            return False
        
        # PDF出力パスを決定
        pdf_output_folder = self.config.get("pdf_output_folder")
        pdf_filename = self.config.get("pdf_filename")
        
        if pdf_filename:
            output_filename = pdf_filename
        else:
            output_filename = f"{self.config['book_title']}.pdf"
        
        if pdf_output_folder:
            output_path = Path(pdf_output_folder) / output_filename
            # 出力フォルダを作成
            Path(pdf_output_folder).mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(output_filename)
        
        # PDF変換コマンドを準備
        cmd = [
            sys.executable, str(self.pdf_converter_script),
            "--input", str(input_folder),
            "--output", str(output_path),
            "--quality", "95",
            "--yes"  # 確認プロンプトをスキップ
        ]
        
        # 設定ファイルから pages_per_pdf を取得して追加
        pages_per_pdf = self.config.get('pages_per_pdf')
        if pages_per_pdf:
            cmd.extend(["--pages-per-pdf", str(pages_per_pdf)])
        
        if dry_run:
            print("【ドライラン】PDF変換をシミュレート")
            print(f"  入力フォルダ: {input_folder}")
            if jpg_output_folder.exists():
                print(f"  （JPGフォルダが存在するため、JPGフォルダを使用します）")
            print(f"  出力ファイル: {output_path}")
            if pages_per_pdf:
                print(f"  分割設定: {pages_per_pdf}ページごとに分割")
            print(f"  実行コマンド: {' '.join(cmd)}")
            return True
        
        try:
            if jpg_output_folder.exists():
                print(f"JPGフォルダが存在するため、JPGフォルダからPDFを作成します: {input_folder}")
            if pages_per_pdf:
                print(f"分割設定: {pages_per_pdf}ページごとにPDFを分割します")
            print(f"実行コマンド: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=True, capture_output=False)
            
            if result.returncode == 0:
                print(f"✓ PDF変換が完了しました: {output_path}")
                return True
            else:
                print(f"✗ PDF変換が失敗しました (終了コード: {result.returncode})")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ PDF変換でエラーが発生しました: {e}")
            return False
        except KeyboardInterrupt:
            print("✗ ユーザーによって中断されました")
            return False
    
    def run_pipeline(self, skip_screenshots: bool = False, skip_png_to_jpg: bool = False, skip_duplicates: bool = False, skip_pdf: bool = False, dry_run: bool = False) -> bool:
        """
        パイプライン全体を実行
        
        Args:
            skip_screenshots: スクリーンショット撮影をスキップ
            skip_png_to_jpg: PNG → JPG変換をスキップ
            skip_duplicates: 重複削除をスキップ
            skip_pdf: PDF変換をスキップ
            dry_run: ドライランモード
            
        Returns:
            全ての処理が成功した場合True
        """
        # 依存関係チェック
        if not self.check_dependencies():
            return False
        
        # パイプライン情報を表示
        self.print_pipeline_info(skip_screenshots, skip_png_to_jpg, skip_duplicates, skip_pdf, dry_run)
        
        if not dry_run:
            print("\n処理を開始します...")
            time.sleep(2)
        
        success = True
        
        # ステップ1: スクリーンショット撮影
        if not skip_screenshots:
            if not self.run_screenshot_capture(dry_run):
                print("✗ スクリーンショット撮影に失敗しました。処理を中止します。")
                return False
        else:
            print("\nステップ 1: スクリーンショット撮影をスキップしました")
        
        # ステップ2: 重複削除
        if not skip_duplicates:
            if not self.run_duplicate_removal(dry_run):
                print("✗ 重複画像削除に失敗しました。処理を中止します。")
                return False
        else:
            print("\nステップ 2: 重複画像削除をスキップしました")
        
        # ステップ3: PNG → JPG変換
        if not skip_png_to_jpg:
            if not self.run_png_to_jpg_conversion(dry_run):
                print("✗ PNG → JPG変換に失敗しました。処理を中止します。")
                return False
        else:
            print("\nステップ 3: PNG → JPG変換をスキップしました")
        
        # ステップ4: PDF変換
        if not skip_pdf:
            if not self.run_pdf_conversion(dry_run):
                print("✗ PDF変換に失敗しました。")
                return False
        else:
            print("\nステップ 4: PDF変換をスキップしました")
        
        # 完了メッセージ
        print("\n" + "=" * 70)
        if dry_run:
            print("✓ ドライラン完了: 全ての処理が正常に実行可能です")
        else:
            print("✓ パイプライン完了: Kindle → PDF 変換が正常に完了しました")
        print("=" * 70)
        
        return True


def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="Kindle → PDF 変換パイプライン",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 全ての処理を実行
  python kindle2pdf.py
  
  # カスタム設定ファイルを使用
  python kindle2pdf.py --config my_config.json
  
  # スクリーンショットをスキップしてPNG→JPG変換、重複削除、PDF変換のみ実行
  python kindle2pdf.py --skip-screenshots
  
  # PNG → JPG変換をスキップ
  python kindle2pdf.py --skip-png-to-jpg
  
  # 重複削除をスキップ
  python kindle2pdf.py --skip-duplicates
  
  # PDF変換をスキップ
  python kindle2pdf.py --skip-pdf
  
  # ドライラン（実際の処理は行わない）
  python kindle2pdf.py --dry-run
  
  # 複数オプションの組み合わせ
  python kindle2pdf.py --skip-screenshots --skip-png-to-jpg --skip-duplicates --skip-pdf --dry-run
        """
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.json",
        help="設定ファイルのパス（デフォルト: config.json）"
    )
    
    parser.add_argument(
        "--skip-screenshots",
        action="store_true",
        help="スクリーンショット撮影をスキップ"
    )
    
    parser.add_argument(
        "--skip-png-to-jpg",
        action="store_true",
        help="PNG → JPG変換をスキップ"
    )
    
    parser.add_argument(
        "--skip-duplicates",
        action="store_true",
        help="重複画像削除をスキップ"
    )
    
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="PDF変換をスキップ"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライランモード（実際の処理は行わず、計画のみ表示）"
    )
    
    return parser.parse_args()


def main():
    """メイン処理"""
    try:
        # コマンドライン引数を解析
        args = parse_arguments()
        
        # パイプラインを初期化
        pipeline = KindleToPdfPipeline(config_file=args.config)
        
        # パイプラインを実行
        success = pipeline.run_pipeline(
            skip_screenshots=args.skip_screenshots,
            skip_png_to_jpg=args.skip_png_to_jpg,
            skip_duplicates=args.skip_duplicates,
            skip_pdf=args.skip_pdf,
            dry_run=args.dry_run
        )
        
        # 終了コードを設定
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n✗ ユーザーによって処理が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 予期しないエラーが発生しました: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
