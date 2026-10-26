# 半角/全角の長押し問題 引き継ぎメモ（テスト用ブランチ専用・PRには含めない）

## 目的
upstream（moonlight-stream/moonlight-qt）へ出すPRとして、Windowsクライアント＋日本語キーボード配列で
**半角/全角キーを長押しするとホストのIMEが高速で切り替わり続ける**問題を、最小の差分で直す。

- 環境: クライアント Windows 11（日本語配列、Microsoft IME）→ ホスト Windows 11（Sunshine 2026.516.143833、キー設定は既定）
- 公式 v6.2.0 でも再現する。1回押しの切り替えは公式でも正常。
- ブランチ（フォーク hinatamaxxx/moonlight-qt）
  - `fix-windows-jis-hankaku-zenkaku`: PR用。upstream master `ac296864` ＋ 修正1コミット。
  - `jp-keyboard-pr-test`: テスト用。PR用 ＋ ビルド用ワークフロー ＋ ログ出力 ＋ このメモ ＋ `local-build.bat`。

## ここまでに試したこと
| 版 | 方法 | 長押しの結果 |
|---|---|---|
| pr-test.1 | 押す/離すの向きを入れ替えて送る | 高速切り替え |
| pr-test.2 | 押した瞬間（SDL_RELEASED）に down→up をまとめて送り、離したとき（SDL_PRESSED）は捨てる | 高速切り替え |
| 今のテスト用ブランチ（未検証） | pr-test.2 ＋ 離すまでの2回目以降の SDL_RELEASED を捨てる（`m_HankakuZenkakuHeld`） | **まだ試していない** |

## 原因の見立て（ログでの確認はまだ）
- fork の調査（`fork/jp-keyboard-v6.2.0` の `docs/windows-sdl3-input.md`）によると、このキーは `VK_DBE_SBCSCHAR`(0xF3) と `VK_DBE_DBCSCHAR`(0xF4) を交互に出し、
  **物理的な押下が WM_KEYUP、離すのが WM_KEYDOWN** として届く。
- 長押しすると、クライアント側の自動リピートで「押下」が何度も届く。これが WM_KEYUP（SDL_RELEASED）として届くので、
  SDL の repeat フラグが付かず、Moonlight の `event->repeat` の除外を通り抜ける、と考えている。
- pr-test.1 では、ホストからはキーが押されっぱなしに見えるため、Sunshine のキーリピートも原因になりうる。

## 次にやること
1. ビルド環境を作る（初回だけ）
   - Visual Studio Build Tools（C++ ワークロード）
   - Qt 6.12.0 msvc2022_64: PyPI 版の aqtinstall 3.3.0 では取得できない。upstream CI と同じ
     `git+https://github.com/miurahr/aqtinstall.git@073e34d7c2ab4ae6961ed7cca690b3abd5ba5a7e` を venv に入れ、
     `aqt install-qt windows desktop 6.12.0 win64_msvc2022_64 -O C:\Qt` を実行する。
   - 依存ライブラリ v19: `setup-deps.ps1` と同じ手順（moonlight-qt-deps の v19 `windows-x64.zip` を `libs\windows` に展開）。
   - ダウンロードの前にユーザーの許可を取ること。
2. `cmd /c local-build.bat` を実行する（初回は約2分、2回目以降は数秒〜1分）。できるもの: `build\dev-x64\deploy\Moonlight.exe`（ポータブル版。初回はペアリングが必要）
3. ユーザーに、配信中に半角/全角を「1回押す」「3秒ほど長押しする」を試してもらい、Moonlight を終了してもらう。
4. `build\dev-x64\deploy\Moonlight-*.log` の `[pr-test]` の行を読む。state（1=PRESSED, 0=RELEASED）、repeat、sym、held の並びから、
   長押し中に届くイベントの実際の並びを確かめる。
5. 長押しで1回だけ切り替わるまで直して、ビルドと確認を繰り返す。
6. 直ったら、ログ出力を除いた修正を PR 用ブランチ `fix-windows-jis-hankaku-zenkaku` に入れる。
   - Windows かつ日本語配列のときだけ有効にし、ほかのキーやOSには触れない。
   - コミット作者は `hinatamaxxx <223820995+hinatamaxxx@users.noreply.github.com>`。
   - upstream への PR はユーザーが自分で出すので、作らない。
