# Moonlight PC v6.2.0 - 日本語入力修正版

Moonlight v6.2.0をベースにした非公式Windows x64版です。現在のソースはsdl2-compat 2.32.74／SDL3 3.4.18を使い、WindowsのRaw Inputからキーの押下・解放を取得します。配信ウィンドウのローカルIMEを明示的に無効化し、日本語の変換処理を接続先に任せます。旧SDL2へ戻す回避版は[fix.3](https://github.com/hinatamaxxx/moonlight-qt/releases/tag/v6.2.0-jp-keyboard-fix.3)で引き続き利用できます。

キーの割り当てと送信フラグは旧フォークを維持しています。半角／全角キーは、WindowsのDBEイベントで解放フラグが立たないため、SDL3側で特殊なメッセージから押下・解放を補正して送ります。補正はこのキーに限定し、通常のRaw Inputやclassic SDL2の従来の処理を維持します。

[SDL3修正版fix.5（検証版）](https://github.com/hinatamaxxx/moonlight-qt/releases/tag/v6.2.0-jp-keyboard-fix.5)のAssetsから`MoonlightPortable-Windows-x64-jp-keyboard-v6.2.0-SDL3.zip`をダウンロードし、新しいフォルダへ展開して`Moonlight.exe`を起動してください。インストールは不要です。[最新安定版](https://github.com/hinatamaxxx/moonlight-qt/releases/latest)は旧SDL2回避版fix.3です。fix.4は文字入力の改善が実機で確認されましたが、半角／全角切り替えに不具合が残っていたため、最終版にはしません。

2026-10-10、SDL3で配信ウィンドウにIMEコンテキストが残る問題を再現し、fix.4でRaw Inputと明示的なIME解除に対応しました。その後、ユーザーの実機で半角／全角キーだけを記録し、解放時にもRaw Inputの解放フラグが立たず、SDL3が押しっぱなしと判断する別の原因を確認しました。fix.5はSDL3 3.4.18のソースに限定的なパッチを適用します。fix.5での接続先IME切り替えは、引き続き実機確認が必要です。

自動テストは取得した半角／全角イベントの200回分の押下・解放、通常キー、リピート除外、フォーカス喪失時の解放、Raw Input登録、IME解除、二重送信防止、ウィンドウ再作成を確認します。配布ZIPのDLLハッシュ、パッチの出所、x64形式、SDL_ttf初期化、Moonlight起動も確認します。設定・ペアリング情報は配布ZIPに含めません。[調査の根拠と確認範囲](docs/windows-sdl3-input.md)も参照してください。

## ビルドと旧SDL2回避版

通常の`powershell ./setup-deps.ps1`はv19依存構成を導入後、`scripts/build-sdl3-jis.bat`でSDL3 3.4.18をパッチ付きでビルドします。Visual Studio 2022または2026とPythonが必要です。CMake 4.4.4は専用キャッシュへ導入します。classic SDL2へ戻して比較する場合のみ`powershell ./setup-deps.ps1 -UseClassicSdl`を指定してください。旧`-UseUpstreamSdl`引数も互換性のため受け付けます。パッチはWindows x64向けです。

旧SDL2回避版は2024年の開発スナップショットを固定するため、SDL3の新しいデバイス対応や後続の修正を取り込めません。そのバイナリは[Moonlightの旧依存ライブラリコミット](https://github.com/cgutman/moonlight-qt-prebuilts/commit/a27d6a7995ef504963fa9058c69e6ba1b449cc0f)（SDLソース`10b4a79379d226041781d0a825da79a296af715f`）由来です。2026-10-09時点の公開記録では、そのWindows x64スナップショットに未修正で該当する既知のCVEは確認できませんでしたが、バイナリ監査は行っていません。SDL3修正版ではこの古いDLLを使用しません。

旧SDL2固定の情報は`scripts/classic-sdl.json`にあります。ARM64はこの旧DLLへ固定しません。配布・実行テストはWindows x64を対象としています。

実装支援：OpenAI Codex。詳細なモデル名と推論設定は記録していません。

## English

This unofficial Windows x64 fork uses Moonlight v6.2.0 with sdl2-compat 2.32.74 and SDL3 3.4.18. It obtains physical keyboard events through Windows Raw Input and explicitly disassociates the local IME from the streaming HWND. Text composition is handled on the host. The earlier classic SDL2 workaround remains available in fix.3.

Legacy mappings and transmission flags are preserved. A narrow SDL3 patch decodes Hankaku/Zenkaku DBE messages before SDL keyboard-state/repeat handling: the captured Windows events lack RI_KEY_BREAK even on release. Ordinary Raw Input and classic SDL2 behavior are unchanged. Normal dependency setup builds patched SDL3 3.4.18 from pinned source; `setup-deps.ps1 -UseClassicSdl` selects the earlier workaround.

Download `MoonlightPortable-Windows-x64-jp-keyboard-v6.2.0-SDL3.zip` from [fix.5 (prerelease)](https://github.com/hinatamaxxx/moonlight-qt/releases/tag/v6.2.0-jp-keyboard-fix.5), extract it into a new folder, and run `Moonlight.exe`. This is a Windows x64 Portable build. The user confirmed improved typing in fix.4, then found its half/full-width toggle defect. fix.5 host IME toggling still needs user confirmation; fix.3 remains stable in the meantime.

On 2026-10-10, a native test reproduced an IME context remaining on the second SDL3 window despite inactive text input and SDL_StopTextInput(). SDL3's IMM initialization retains the first window. The fix disables the actual streaming HWND's IME and bypasses IME-modified WM_KEY input. Tests cover real Raw Input registration, IME exclusion, WM_KEY deduplication, window recreation, captured transport, package hashes and startup. The original live-stream symptoms have not been fully reproduced automatically; live Japanese typing with this SDL3 build still needs confirmation. See [investigation details](docs/windows-sdl3-input.md).

The SDL3 build retains version 3.4.18 with a clearly marked JIS patch; other dependencies remain v19. The captured DBE sequence passes 200 balanced press/release cycles in a test compiled from the exact patched decoder. Package metadata records source, patch and DLL hashes. The optional classic SDL2 fallback retains a fixed 2024 snapshot and misses later fixes. No applicable unresolved CVE was identified in the public records reviewed on 2026-10-09, which was not a binary security audit. Windows x64 is the tested package target.

Implementation assistance: OpenAI Codex. Exact model variant and reasoning setting were not recorded.

---

# Moonlight PC (upstream documentation)

[Moonlight PC](https://moonlight-stream.org) is an open source PC client for NVIDIA GameStream and [Sunshine](https://github.com/LizardByte/Sunshine).

Moonlight also has mobile versions for [Android](https://github.com/moonlight-stream/moonlight-android) and [iOS](https://github.com/moonlight-stream/moonlight-ios).

You can follow development on our [Discord server](https://moonlight-stream.org/discord) and help translate Moonlight into your language on [Weblate](https://hosted.weblate.org/projects/moonlight/moonlight-qt/).

 [![Build](https://img.shields.io/github/actions/workflow/status/moonlight-stream/moonlight-qt/build.yml?branch=master)](https://github.com/moonlight-stream/moonlight-qt/actions/workflows/build.yml?query=branch%3Amaster)
 [![Downloads](https://img.shields.io/github/downloads/moonlight-stream/moonlight-qt/total)](https://github.com/moonlight-stream/moonlight-qt/releases)
 [![Translation Status](https://hosted.weblate.org/widgets/moonlight/-/moonlight-qt/svg-badge.svg)](https://hosted.weblate.org/projects/moonlight/moonlight-qt/)

## Features
 - Hardware accelerated video decoding on Windows, Mac, and Linux
 - H.264, HEVC, and AV1 codec support (AV1 requires Sunshine and a supported host GPU)
 - YUV 4:4:4 support (Sunshine only)
 - HDR streaming support
 - 7.1 surround sound audio support
 - 10-point multitouch support (Sunshine only)
 - Gamepad support with force feedback and motion controls for up to 16 players
 - Support for both pointer capture (for games) and direct mouse control (for remote desktop)
 - Support for passing system-wide keyboard shortcuts like Alt+Tab to the host
 
## Downloads
- [Windows, macOS, and Steam Link](https://github.com/moonlight-stream/moonlight-qt/releases)
- [Snap (for Ubuntu-based Linux distros)](https://snapcraft.io/moonlight)
- [Flatpak (for other Linux distros)](https://flathub.org/apps/details/com.moonlight_stream.Moonlight)
- [AppImage](https://github.com/moonlight-stream/moonlight-qt/releases)
- [Raspberry Pi 4 and 5](https://github.com/moonlight-stream/moonlight-docs/wiki/Installing-Moonlight-Qt-on-Raspberry-Pi-4)
- [Generic ARM 32-bit and 64-bit Debian packages](https://github.com/moonlight-stream/moonlight-docs/wiki/Installing-Moonlight-Qt-on-ARM%E2%80%90based-Single-Board-Computers) (not for Raspberry Pi)
- [Experimental RISC-V Debian packages](https://github.com/moonlight-stream/moonlight-docs/wiki/Installing-Moonlight-Qt-on-RISC%E2%80%90V-Single-Board-Computers)
- [NVIDIA Jetson and Nintendo Switch (Ubuntu L4T)](https://github.com/moonlight-stream/moonlight-docs/wiki/Installing-Moonlight-Qt-on-Linux4Tegra-(L4T)-Ubuntu)

### Nightly Builds
- [Downloads](https://nightly.link/moonlight-stream/moonlight-qt/workflows/build/master)

#### Special Thanks

[![Hosted By: Cloudsmith](https://img.shields.io/badge/OSS%20hosting%20by-cloudsmith-blue?logo=cloudsmith&style=flat-square)](https://cloudsmith.com)

Hosting for Moonlight's Debian and L4T package repositories is graciously provided for free by [Cloudsmith](https://cloudsmith.com).

## Building

### Windows Build Requirements
* Qt 6.11 SDK or later (earlier versions may work but are not officially supported)
* [Visual Studio 2026](https://visualstudio.microsoft.com/downloads/) (Community edition is fine)
* Select **MSVC** option during Qt installation. MinGW is not supported.
* [7-Zip](https://www.7-zip.org/) (only if building installers for non-development PCs)
* Graphics Tools (only if running debug builds)
  * Install "Graphics Tools" in the Optional Features page of the Windows Settings app.
  * Alternatively, run `dism /online /add-capability /capabilityname:Tools.Graphics.DirectX~~~~0.0.1.0` and reboot.

### macOS Build Requirements
* Qt 6.11 SDK or later (earlier versions may work but are not officially supported)
* Xcode 15 or later (earlier versions may work but are not officially supported)
* [create-dmg](https://github.com/sindresorhus/create-dmg) (only if building DMGs for use on non-development Macs)

### Linux/Unix Build Requirements
* Qt 6 is recommended, but Qt 5.12 or later is also supported (replace `qmake6` with `qmake` when using Qt 5).
* GCC or Clang
* FFmpeg 4.0 or later
* Install the required packages:
  * Debian/Ubuntu:
    * Base Requirements: `libegl1-mesa-dev libgl1-mesa-dev libopus-dev libsdl2-dev libsdl2-ttf-dev libssl-dev libavcodec-dev libavformat-dev libswscale-dev libva-dev libvdpau-dev libxkbcommon-dev wayland-protocols libdrm-dev`
    * Qt 6 (Recommended): `qt6-base-dev qt6-declarative-dev libqt6svg6-dev qt6-wayland qml6-module-qtquick-controls qml6-module-qtquick-templates qml6-module-qtquick-layouts qml6-module-qtqml-workerscript qml6-module-qtquick-window qml6-module-qtquick`
    * Qt 5: `qtbase5-dev qt5-qmake qtdeclarative5-dev qtquickcontrols2-5-dev qml-module-qtquick-controls2 qml-module-qtquick-layouts qml-module-qtquick-window2 qml-module-qtquick2 qtwayland5`
  * RedHat/Fedora (RPM Fusion repo required):
    * Base Requirements: `openssl-devel SDL2-devel SDL2_ttf-devel ffmpeg-devel libva-devel libvdpau-devel opus-devel pulseaudio-libs-devel alsa-lib-devel libdrm-devel`
    * Qt 6 (Recommended): `qt6-qtsvg-devel qt6-qtdeclarative-devel`
    * Qt 5: `qt5-qtsvg-devel qt5-qtquickcontrols2-devel`
* Building the Vulkan renderer requires a `libplacebo-dev`/`libplacebo-devel` version of at least v7.349.0 and FFmpeg 6.1 or later.

### Steam Link Build Requirements
* [Steam Link SDK](https://github.com/ValveSoftware/steamlink-sdk) cloned on your build system
* STEAMLINK_SDK_PATH environment variable set to the Steam Link SDK path

**Steam Link Hardware Limitations**  
Moonlight builds for Steam Link are subject to hardware limitations of the Steam Link device:
* Maximum resolution: **1080p (1920x1080)**
* Maximum framerate: **60 FPS**
* Maximum video bitrate: **40 Mbps**
* **HDR streaming is not supported** on the original hardware

### Docker containers
If you want to use Docker for building, look at [this repo](https://github.com/cgutman/moonlight-packaging) containing canonical containers
for different architectures, which handle building deps and extra linking for you.

### Build Setup Steps
1. Install the latest Qt SDK (and optionally, the Qt Creator IDE) from https://www.qt.io/download
    * You can install Qt via Homebrew on macOS, but you will need to use `brew install qt --with-debug` to be able to create debug builds of Moonlight.
    * You may also use your Linux distro's package manager for the Qt SDK as long as the packages are Qt 5.12 or later.
    * This step is not required for building on Steam Link, because the Steam Link SDK includes Qt 5.14.
2. Download submodules and dependencies
    * Run `git submodule update --init --recursive` from within `moonlight-qt/`.
    * On Windows and macOS, you must also run `setup-deps.ps1` (Windows) or `setup-deps.py` (macOS).
    * Perform these steps each time you pull new changes from the Git repository.
3. Open the project in Qt Creator or build from qmake on the command line.
    * To build a binary for use on non-development machines, use the scripts in the `scripts` folder.
        * For Windows builds, use `scripts\build-arch.bat` and `scripts\generate-bundle.bat`. Execute these scripts from the root of the repository within a Qt command prompt. Ensure  7-Zip binary directory is on your `%PATH%`.
        * For macOS builds, use `scripts/generate-dmg.sh`. Execute this script from the root of the repository and ensure Qt's `bin` folder is in your `$PATH`.
        * For Steam Link builds, run `scripts/build-steamlink-app.sh` from the root of the repository.
    * To build from the command line for development use on macOS or Linux, run `qmake6 moonlight-qt.pro` then `make debug` or `make release`.
        * The final binary will be placed in `app/moonlight`.
    * To create an embedded build for a single-purpose device, use `qmake6 "CONFIG+=embedded" moonlight-qt.pro` and build normally.
        * This build will lack windowed mode, Discord/Help links, and other features that don't make sense on an embedded device.
        * For platforms with poor GPU performance, add `"CONFIG+=gpuslow"` to prefer direct KMSDRM rendering over GL/Vulkan renderers. Direct KMSDRM rendering can use dedicated YUV/RGB conversion and scaling hardware rather than slower GPU shaders for these operations.

## Contribute
1. Fork us
2. Write code
3. Send Pull Requests

Check out our [website](https://moonlight-stream.org) for project links and information.
