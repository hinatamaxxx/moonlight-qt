# Moonlight PC v6.2.0 - 日本語入力修正版

Moonlight v6.2.0をベースに、日本語入力中の文字連打・文字抜けを改善する非公式Windows x64版です。旧フォークのキーボード処理に加え、実行時の`SDL2.dll`を正常だったv6.1.0修正版と同じclassic SDL 2.31.0へ固定します。公式v6.2.0の依存ライブラリにあるsdl2-compat／SDL3経由の入力処理を回避します。

キーの割り当て、送信フラグ、半角／全角キーの押下・解放反転を旧版にそろえています。旧版と同じく、反転処理は日本語配列以外や他のOSでも適用されます。v6.2.0のストリーミング操作とキー解放管理は維持しています。旧版以降に追加された変換・無変換キーの割り当てと拡張キーのフラグは、この入力処理では使いません。

[最新の修正版リリース](https://github.com/hinatamaxxx/moonlight-qt/releases/latest)のAssetsから`MoonlightPortable-Windows-x64-jp-keyboard-v6.2.0.zip`をダウンロードし、新しいフォルダへ展開して`Moonlight.exe`を起動してください。Windows x64向けのPortable版で、インストールは不要です。

2026-10-09、Windows 11クライアント→Windows 11ホストで、使用者から日本語入力の連打・文字抜けが改善したとの報告がありました。確認したIME製品・バージョンは記録していません。他の環境での改善や、SDL3側の具体的な原因は未確認です。半角／全角の長押しでIMEが高速に切り替わる旧版の問題は残る可能性があります。

送信イベントの旧版との一致とフォーカス喪失時のキー解放に加え、配布ZIPのSDL2.dllのSHA256、x64形式、非表示ウィンドウ作成、SDL_ttf初期化、Moonlightの起動を自動確認します。設定・ペアリング情報は配布ZIPに含めません。

## ライブラリの変更と制約

`SDL2.dll`だけを旧版へ固定し、Moonlight本体・映像デコード・OpenSSLなどはv6.2.0の構成を使います。現在のSDL3系のコントローラー対応や、後続SDL2のクラッシュ修正などは取り込めません。SDL2の開発スナップショットを固定するため、将来の修正を自動では受け取れません。[SDL公式はSDL3への移行を推奨しています](https://github.com/libsdl-org/SDL/releases/tag/release-2.32.0)。この回避策は長期的な保守の代わりにはなりません。

使用するバイナリの由来は[Moonlightの旧依存ライブラリコミット](https://github.com/cgutman/moonlight-qt-prebuilts/commit/a27d6a7995ef504963fa9058c69e6ba1b449cc0f)（SDLソース`10b4a79379d226041781d0a825da79a296af715f`、2024-09-02）です。旧配布ZIPとDLLの両方をSHA256で検証します。[SDLの公開セキュリティ情報](https://github.com/libsdl-org/SDL/security)と[libsdl2のCVE記録](https://security-tracker.debian.org/tracker/source-package/libsdl2)を確認しましたが、このWindows x64スナップショットに未修正で該当する既知のCVEは確認できていません。独立したバイナリ監査は行っておらず、安全性を保証するものではありません。

Windows x64の通常ビルドは`powershell ./setup-deps.ps1`で同じDLLを導入します。固定内容は`scripts/classic-sdl.json`にあります。SDL3経由の動作を調査する場合は`powershell ./setup-deps.ps1 -UseUpstreamSdl`で上流の依存構成に戻せます。ARM64とmacOSにはこのDLL変更を適用しません。

実装支援：OpenAI Codex。詳細なモデル名と推論設定は記録していません。

## English

This unofficial Windows x64 fork keeps Moonlight v6.2.0, restores keyboard event handling from the v6.1.0 fork (commit `c13f4a21507b5097d48d9e643b162786336ce982`), and pins the runtime SDL2.dll to the same classic SDL 2.31.0 binary as that release. This bypasses the sdl2-compat/SDL3 input backend.

The source branch now uses the previous key mappings, transmission flags, and unconditional Hankaku/Zenkaku event reversal. This also restores the previous behavior on non-Japanese layouts and other platforms. The v6.2.0 stream controls and held-key release mechanism remain available. Conversion-key mappings and extended-key flags added after the old fork are no longer applied by this handler.

Download `MoonlightPortable-Windows-x64-jp-keyboard-v6.2.0.zip` from the [latest release](https://github.com/hinatamaxxx/moonlight-qt/releases/latest), extract it into a new folder, and run `Moonlight.exe`. This is a Windows x64 Portable build; no installation is required.

On 2026-10-09, the user reported improved Japanese typing on a Windows 11 client and Windows 11 host. The IME product/version was not recorded. This is one environment; the underlying SDL3 bug is not isolated. Tests cover input-event parity, focus-loss release, the pinned DLL hash, x64 format, hidden-window creation, SDL_ttf and Moonlight startup. The old issue with rapid IME toggling when holding Hankaku/Zenkaku may remain.

Only the x64 SDL2 runtime is pinned. Other dependencies stay on the v6.2.0 dependency set. New SDL3 device support and later SDL2 bug fixes are unavailable; the fixed 2024 development snapshot does not receive automatic maintenance. No known unresolved CVE applicable to this Windows snapshot was identified in the public records reviewed, but this is not a binary security audit. SDL upstream recommends migration to SDL3. Use `setup-deps.ps1 -UseUpstreamSdl` to investigate the upstream backend. ARM64/macOS are unchanged by the runtime pin.

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
