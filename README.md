# Moonlight PC（Windows 日本語入力 & ノート PC 運用向けフォーク）

[moonlight-stream/moonlight-qt](https://github.com/moonlight-stream/moonlight-qt)（v6.2.0 / `master` ベース）の非公式 Windows 向けフォークです。

Windows クライアントでの **日本語入力の不具合修正** と、**ノート PC の蓋閉じスリープ運用を快適にする自動再接続機能** を追加しています。SDL3 本体の独自パッチや Raw Input 強制を使わない最小限の構成で実装しています。

---

## 主な改善・追加機能

### 1. 日本語入力の改善（Windows）

- **文字抜け・連打の解消（ローカル IME の確実な無効化）**
  - 本家 Moonlight（SDL3）では起動時の隠しデコーダウィンドウにしか `IME_Disable()` が効かず、配信ウィンドウにローカル Windows の IME が残って入力を横取りする問題があります。
  - 配信ウィンドウの HWND に対して直接 `ImmAssociateContextEx(hwnd, nullptr, 0)` を適用（ウィンドウ作成時・フォーカス復帰時・フルスクリーン切替時・デコーダ生成後）することで、ローカル IME の干渉を完全に解消しました。
  - SDL3 への独自パッチや Raw Input 強制を使わないため、`Ctrl+C` / `Ctrl+V` / `Ctrl+A` / `Shift+矢印` などの修飾キー同時押しも正常に動作します。
- **半角/全角キーの単押し・長押し修正**
  - Windows 日本語配列では半角/全角キー（`SDL_SCANCODE_GRAVE`）の押下・解放が反転して届き、長押しすると自動リピートでホストの IME が高速切替され続ける問題があります。
  - 初回押下時に `DOWN → UP` を 1 タップ送信し、物理的に離す（またはフォーカス喪失）まで後続のリピートを無視するように修正しました。1 回押しでも長押しでもホストの IME が **1 回だけ** 切り替わります。
- **Windows JIS 専用キーの追加**
  - `変換`（`0x1C`）・`無変換`（`0x1D`）・`カタカナ/ひらがな`（`0xF2`）を `SS_KBE_FLAG_NON_NORMALIZED` 付きで送信するように追加しました（本家の `¥` / `ろ(_)` 対応も維持）。

### 2. ノート PC 運用向けの機能追加・改善

- **スリープ / 蓋閉じ復帰時の自動再接続**
  - 配信中にノート PC を閉じてスリープ → 再度開いてスリープ解除した際、エラーダイアログを出さずに自動でストリームを再開します。
  - Windows 公式 API `PowerRegisterSuspendResumeNotification`（通常スリープ S3・モダンスタンバイ S0ix 両対応）と、配信ループ内の時刻ジャンプ検知（5 秒以上）の 2 重構成でスリープ復帰を確実に検知します。
  - 復帰を検知した時点で死んだ接続を即座に終了し（ホスト側アプリは終了させません）、Wi-Fi や VPN の再接続を待ちながら **約 2 秒おきに最大 15 回（約 30 秒間）** 自動で再接続を試行します。ホスト側でアプリが生きていれば `resume`、終了していれば自動で `launch` にフォールバックします。
  - 再接続中は `Esc` キーまたは `Cancel` ボタンでいつでも中止できます。`Ctrl+Alt+Shift+Q` などの通常終了時は再接続しません。
  - Windows の自動ログインと組み合わせることで、ノート PC の蓋を開くだけでそのままホスト PC のデスクトップへシームレスに復帰できます。

---

## ダウンロードと使い方（Windows x64 Portable）

1. [Releases](https://github.com/hinatamaxxx/moonlight-qt/releases/latest) から `MoonlightPortable-Windows-x64-*.zip` をダウンロードします。
2. 任意のフォルダに展開し、`Moonlight.exe` を起動します。
   - `portable.dat` 同梱のため、設定とペアリング情報は展開したフォルダ内に保存されます（既存の Moonlight 環境を上書きしません）。

---

## 本家（upstream）への PR 状況

日本語入力の修正は本家 `moonlight-stream/moonlight-qt` にも独立した PR として提出しています。

- ローカル Windows IME の無効化: [moonlight-stream/moonlight-qt#2108](https://github.com/moonlight-stream/moonlight-qt/pull/2108)
- 半角/全角キーの修正: [moonlight-stream/moonlight-qt#2109](https://github.com/moonlight-stream/moonlight-qt/pull/2109)

---

## 本家 Moonlight PC について

Moonlight PC 本体・対応プラットフォーム・ビルド手順の詳細は、本家リポジトリ [moonlight-stream/moonlight-qt](https://github.com/moonlight-stream/moonlight-qt) を参照してください。
