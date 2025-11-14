import time
import pyautogui
import os
import sys
import argparse
import json
import platform
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim

# OS自動判定
CURRENT_OS = platform.system().lower()
print(f"検出されたOS: {CURRENT_OS}")

# OS別の設定
if CURRENT_OS == 'darwin':  # macOS
    pyautogui.FAILSAFE = True  # フェイルセーフを有効にする（マウスを左上角に移動すると停止）
    pyautogui.PAUSE = 0.5      # 操作間の待機時間を設定
    print("macOS用設定を適用しました")
elif CURRENT_OS == 'windows':  # Windows
    pyautogui.FAILSAFE = True  # フェイルセーフを有効にする
    pyautogui.PAUSE = 0.3      # Windows用の待機時間（少し短め）
    print("Windows用設定を適用しました")
else:
    # Linux等その他のOS
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
    print(f"汎用設定を適用しました（OS: {CURRENT_OS}）")

def check_permissions():
    """
    OS別の権限チェック（強化版）
    """
    import tempfile
    
    try:
        # テストスクリーンショット
        print("スクリーンショット権限をテスト中...")
        test_screenshot = pyautogui.screenshot()
        
        # 一時ファイルに保存してテスト
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_screenshot.save(tmp_file.name)
            if os.path.exists(tmp_file.name):
                file_size = os.path.getsize(tmp_file.name)
                os.unlink(tmp_file.name)  # テストファイルを削除
                print(f"スクリーンショット権限: OK (テストファイルサイズ: {file_size} bytes)")
                return True
            else:
                print("スクリーンショット保存権限: NG")
                return False
                
    except Exception as e:
        print(f"権限エラー: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        
        if CURRENT_OS == 'darwin':  # macOS
            print("\nmacOS権限設定:")
            print("1. システム環境設定 → セキュリティとプライバシー → プライバシー")
            print("2. 「画面録画」でPythonまたはターミナルを許可")
            print("3. 「アクセシビリティ」でPythonまたはターミナルを許可")
            print("4. 設定変更後、ターミナルを再起動してください")
        elif CURRENT_OS == 'windows':  # Windows
            print("\nWindows権限設定:")
            print("1. 管理者権限でコマンドプロンプトまたはPowerShellを実行")
            print("2. ウイルス対策ソフトがpyautoguiをブロックしていないか確認")
            print("3. Windows Defenderの例外設定を確認")
        else:
            print("\n権限設定:")
            print("X11またはWaylandの権限設定を確認してください。")
        
        return False

def load_config(config_file=None):
    """
    設定ファイルを読み込む関数
    Args:
        config_file (str, optional): 設定ファイルのパス
    Returns:
        dict: 設定辞書
    """
    default_config = {
        "output_folder": os.path.join(os.path.expanduser("~"), "Documents"),
        "book_title": "KindleBook",
        "page_delay": 2,
        "num_pages": 100,
        "similarity_threshold": 0.99
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                print(f"設定ファイル '{config_file}' を読み込みました。")
                print(f"読み込んだ設定: {user_config}")
                # デフォルト設定にユーザー設定をマージ
                default_config.update(user_config)
                print(f"マージ後の設定: {default_config}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            print("デフォルト設定を使用します。")
    elif config_file:
        print(f"設定ファイルが見つかりません: {config_file}")
        print("デフォルト設定を使用します。")
    else:
        print("設定ファイルが指定されていません。デフォルト設定を使用します。")
    
    return default_config

def load_and_resize_image(image_path, target_size=(256, 256)):
    """
    画像を読み込み、比較用にリサイズ・グレースケール変換
    
    Args:
        image_path: 画像ファイルのパス
        target_size: リサイズ後のサイズ
        
    Returns:
        グレースケール画像の配列、失敗時はNone
    """
    try:
        with Image.open(image_path) as img:
            # RGBAの場合はRGBに変換
            if img.mode == 'RGBA':
                # 白背景で合成
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # リサイズ
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # グレースケールに変換
            img_gray = img.convert('L')
            
            # numpy配列に変換
            return np.array(img_gray)
            
    except Exception as e:
        print(f"画像の読み込みに失敗しました: {image_path} - {e}")
        return None

def compare_images(image_path1, image_path2, similarity_threshold=0.99):
    """
    2つの画像の類似度をSSIMで計算し、閾値以上かどうかを判定する関数
    
    Args:
        image_path1 (str): 比較する画像1のパス
        image_path2 (str): 比較する画像2のパス
        similarity_threshold (float): 類似度の閾値（0.0-1.0、デフォルト: 0.99）
    Returns:
        bool: 類似度が閾値以上の場合True、未満の場合False
    """
    try:
        if not os.path.exists(image_path1) or not os.path.exists(image_path2):
            return False
        
        # 画像を読み込み、リサイズ・グレースケール変換
        img1 = load_and_resize_image(image_path1)
        img2 = load_and_resize_image(image_path2)
        
        if img1 is None or img2 is None:
            return False
        
        # SSIMを計算
        similarity = ssim(img1, img2, data_range=255)
        
        return similarity >= similarity_threshold
    except Exception as e:
        print(f"画像比較エラー: {e}")
        return False

def capture_kindle_screenshots(book_title="KindleBook", page_delay=2, num_pages=None, output_folder=None, similarity_threshold=0.99):
    """
    Kindle本のスクリーンショットを自動化する関数（macOS対応版）
    Args:
        book_title (str, optional): スクリーンショットの保存フォルダ名。デフォルトは "KindleBook"。
        page_delay (int, optional): ページをめくる操作後の待機時間（秒）。デフォルトは 2 秒。
        num_pages (int, optional): キャプチャするページ数。None の場合は、指定された方法でページめくりが止まるまでキャプチャを続ける。
        output_folder (str, optional): 保存先のベースフォルダ。指定されない場合はデフォルトを使用。
        similarity_threshold (float, optional): 画像類似度の閾値（0.0-1.0）。デフォルトは 0.99。
    """
    # 権限チェック
    if not check_permissions():
        print("必要な権限が不足しています。処理を中止します。")
        return
    
    # 保存フォルダを作成
    if output_folder is None:
        output_folder = os.path.join(os.path.expanduser("~"), "Documents")
    
    full_output_path = os.path.join(output_folder, book_title)
    
    try:
        os.makedirs(full_output_path, exist_ok=True)
        
        # 書き込み権限をテスト
        test_file = os.path.join(full_output_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        print(f"スクリーンショットを保存するフォルダ: {full_output_path}")
        print("フォルダの書き込み権限: OK")
        
    except PermissionError as e:
        print(f"フォルダ権限エラー: {e}")
        print(f"フォルダパス: {full_output_path}")
        print("別の保存先を試します...")
        
        # 代替保存先を試す
        alternative_path = os.path.join(os.path.expanduser("~"), "Documents", book_title)
        try:
            os.makedirs(alternative_path, exist_ok=True)
            full_output_path = alternative_path
            print(f"代替保存先: {full_output_path}")
        except Exception as e2:
            print(f"代替保存先も失敗: {e2}")
            return
            
    except Exception as e:
        print(f"フォルダ作成エラー: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"フォルダパス: {full_output_path}")
        return

    # Kindleアプリがアクティブであることを確認
    print("Kindleアプリがアクティブで、最初のページが表示されていることを確認してください。")
    print("注意: マウスを画面左上角に移動すると処理が停止します（フェイルセーフ機能）")
    
    # OS別のページめくり方法を表示
    if CURRENT_OS == 'darwin':  # macOS
        print("macOS用ページめくり方法を試します：")
        print("1. スペースキー")
        print("2. 右矢印キー")
        print("3. 画面右側クリック")
    elif CURRENT_OS == 'windows':  # Windows
        print("Windows用ページめくり方法を試します：")
        print("1. 右矢印キー")
        print("2. スペースキー")
        print("3. 画面右側クリック")
        print("4. PageDownキー")
    else:
        print("汎用ページめくり方法を試します：")
        print("1. 右矢印キー")
        print("2. スペースキー")
        print("3. 画面右側クリック")
    
    input("準備ができたらEnterキーを押してください...")

    # カウントダウン処理
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("キャプチャを開始します。")

    page_count = 0
    consecutive_failures = 0
    previous_screenshot_path = None
    consecutive_same_images = 0
    max_consecutive_same = 10  # 同じ画像が連続する最大回数
    
    while True:
        page_count += 1
        # ページ数を指定した場合の処理
        if page_count > num_pages:
            print(f"指定されたページ数（{num_pages}ページ）に達しました。キャプチャを終了します。")
            break

        try:
            # スクリーンショットを保存
            screenshot_path = os.path.join(full_output_path, f"page_{page_count:04d}.png")
            
            print(f"ページ {page_count} のスクリーンショットを撮影中...")
            
            # スクリーンショット撮影
            screenshot = pyautogui.screenshot()
            
            # ファイル保存
            screenshot.save(screenshot_path)
            
            # ファイルが実際に保存されたか確認
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                if file_size > 0:
                    print(f"✓ ページ {page_count} をキャプチャしました")
                    print(f"  保存先: {screenshot_path}")
                    print(f"  ファイルサイズ: {file_size:,} bytes")
                    consecutive_failures = 0  # 成功したらカウンターをリセット
                    
                    # 前回の画像と比較
                    if previous_screenshot_path is not None:
                        if compare_images(previous_screenshot_path, screenshot_path, similarity_threshold):
                            consecutive_same_images += 1
                            print(f"  ⚠ 前回の画像と類似しています（連続: {consecutive_same_images}/{max_consecutive_same}回、閾値: {similarity_threshold:.1%}）")
                            if consecutive_same_images >= max_consecutive_same:
                                print(f"\n同じ画像が{max_consecutive_same}回連続しました。キャプチャを終了します。")
                                break
                        else:
                            consecutive_same_images = 0  # 異なる画像ならカウンターをリセット
                            print(f"  ✓ 新しい画像です")
                    
                    # 現在の画像を前回の画像として保存
                    previous_screenshot_path = screenshot_path
                else:
                    print(f"✗ エラー: ファイルサイズが0です: {screenshot_path}")
                    consecutive_failures += 1
            else:
                print(f"✗ エラー: ファイルが保存されませんでした: {screenshot_path}")
                consecutive_failures += 1

            # OS別のページめくり操作
            page_turn_success = False
            
            if CURRENT_OS == 'darwin':  # macOS
                # macOS用ページめくり方法
                methods = [
                    ('space', 'スペースキー'),
                    ('right', '右矢印キー'),
                    ('click', '画面右側クリック')
                ]
            elif CURRENT_OS == 'windows':  # Windows
                # Windows用ページめくり方法
                methods = [
                    ('right', '右矢印キー'),
                    ('space', 'スペースキー'),
                    ('click', '画面右側クリック'),
                    ('pagedown', 'PageDownキー')
                ]
            else:
                # その他のOS用ページめくり方法
                methods = [
                    ('right', '右矢印キー'),
                    ('space', 'スペースキー'),
                    ('click', '画面右側クリック')
                ]
            
            # 各方法を順番に試す
            for method, method_name in methods:
                if page_turn_success:
                    break
                    
                try:
                    if method == 'click':
                        screen_width, screen_height = pyautogui.size()
                        click_x, click_y = screen_width * 0.8, screen_height * 0.5
                        print(f"  試行中: {method_name} (座標: {click_x:.0f}, {click_y:.0f})")
                        pyautogui.click(click_x, click_y)
                    else:
                        print(f"  試行中: {method_name}")
                        pyautogui.press(method)
                    page_turn_success = True
                    print(f"  ✓ ページめくり成功: {method_name}")
                    break  # 成功したらループを抜ける
                except Exception as e:
                    print(f"  ✗ ページめくり失敗 ({method_name}): {e}")
                    continue
            
            if not page_turn_success:
                print("ページめくりに失敗しました。手動でページをめくってください。")
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("連続してページめくりに失敗しました。処理を中止します。")
                    break
            
            time.sleep(page_delay)

        except pyautogui.FailSafeException:
            print("✗ フェイルセーフが作動しました。処理を停止します。")
            print("  マウスが画面左上角に移動されました。")
            break
        except PermissionError as e:
            print(f"✗ 権限エラー: {e}")
            print("  スクリーンショット保存権限を確認してください。")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("連続して権限エラーが発生しました。処理を中止します。")
                break
            time.sleep(1)
        except OSError as e:
            print(f"✗ ファイルシステムエラー: {e}")
            print(f"  保存先: {screenshot_path}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("連続してファイルシステムエラーが発生しました。処理を中止します。")
                break
            time.sleep(1)
        except Exception as e:
            print(f"✗ 予期しないエラーが発生しました: {e}")
            print(f"  エラータイプ: {type(e).__name__}")
            print(f"  ページ数: {page_count}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("連続してエラーが発生しました。処理を中止します。")
                break
            time.sleep(1)  # エラー時は少し待機

        # 無限ループ防止
        if page_count > 2000:
            print("2000ページを超えました。強制終了します。")
            break

def parse_arguments():
    """
    コマンドライン引数を解析する関数
    """
    parser = argparse.ArgumentParser(
        description="Kindle本のスクリーンショットを自動化するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python kindless.py -t "マイブック" -p 100 -d 3
  python kindless.py --title "小説" --pages 50 --delay 1
  python kindless.py -o "/Users/username/Desktop/Screenshots" -t "本のタイトル"
  python kindless.py --output "/path/to/folder" --config config.json
  python kindless.py -s 0.95 --similarity 0.98
        """
    )
    
    parser.add_argument(
        "-t", "--title",
        type=str,
        default="KindleBook",
        help="本のタイトル（保存フォルダ名）。デフォルト: KindleBook"
    )
    
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=100,
        help="キャプチャするページ数。指定しない場合は手動停止まで継続"
    )
    
    parser.add_argument(
        "-d", "--delay",
        type=int,
        default=2,
        help="ページめくり後の待機時間（秒）。デフォルト: 2秒"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="設定ファイルのパス（JSON形式）"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="出力フォルダのパス。指定しない場合は設定ファイルまたはデフォルト（~/Documents）を使用"
    )
    
    parser.add_argument(
        "-s", "--similarity",
        type=float,
        default=None,
        help="画像類似度の閾値（0.0-1.0）。デフォルト: 0.99"
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    # コマンドライン引数を解析
    args = parse_arguments()
    
    # 設定ファイルを読み込み
    config_file_path = args.config if args.config else "config.json"
    config = load_config(config_file_path)
    
    print(f"\n設定確認:")
    print(f"  設定ファイルパス: {config_file_path}")
    print(f"  読み込まれた設定: {config}")
    
    # コマンドライン引数で設定を上書き（引数が指定された場合）
    book_title = args.title if args.title != "KindleBook" else config.get("book_title", "KindleBook")
    page_delay = args.delay if args.delay != 2 else config.get("page_delay", 2)
    num_pages = args.pages if args.pages != 100 else config.get("num_pages", 100)
    
    # 類似度の優先度: コマンドライン引数 > 設定ファイル > デフォルト
    if args.similarity is not None:
        similarity_threshold = args.similarity
        if not 0.0 <= similarity_threshold <= 1.0:
            print("エラー: 類似度閾値は0.0から1.0の間で指定してください。")
            sys.exit(1)
    else:
        similarity_threshold = config.get("similarity_threshold", 0.99)
    
    # 出力フォルダの優先度: コマンドライン引数 > 設定ファイル > デフォルト
    print(f"\n出力フォルダの決定:")
    print(f"  コマンドライン引数(-o): {args.output}")
    print(f"  設定ファイルの値: {config.get('output_folder')}")
    
    if args.output:
        output_folder = args.output
        print(f"  → 採用: コマンドライン指定 '{output_folder}'")
    elif config.get("output_folder"):
        output_folder = config.get("output_folder")
        print(f"  → 採用: 設定ファイル '{output_folder}'")
    else:
        output_folder = None  # デフォルト（~/Documents）を使用
        print(f"  → 採用: デフォルト '~/Documents'")
    
    # 引数を使用してスクリーンショット処理を実行
    print("=" * 50)
    print("Kindle スクリーンショット自動化ツール")
    print("=" * 50)
    print(f"本のタイトル: {book_title}")
    print(f"ページ数: {num_pages}")
    print(f"ページ間隔: {page_delay}秒")
    print(f"類似度閾値: {similarity_threshold:.1%}")
    print(f"保存先: {output_folder}")
    print("=" * 50)
    
    try:
        capture_kindle_screenshots(
            book_title=book_title,
            page_delay=page_delay,
            num_pages=num_pages,
            output_folder=output_folder,
            similarity_threshold=similarity_threshold
        )
        print("\n" + "=" * 50)
        print("✓ 処理が正常に完了しました。")
        print("=" * 50)
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("✗ ユーザーによって処理が中断されました。")
        print("=" * 50)
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ 予期しないエラーで処理が中断されました: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        print("=" * 50)
