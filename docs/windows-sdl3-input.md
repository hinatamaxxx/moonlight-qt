# Windows SDL3 keyboard investigation (2026-10-10)

The user's Windows 11 → Windows 11 Japanese typing produced repeated and
missing characters with fix.2, and improved when the same executable used
classic SDL 2.31.0 in fix.3. That isolates a dependency-sensitive regression,
but does not by itself identify which IME messages were lost.

## Confirmed native defect

The exact SDL3 3.4.18 DLL in Moonlight dependency release v19 was tested on
the client. The test initializes video, stops text input, creates a hidden
decoder-test window, then creates a second hidden streaming window.

| Window | After creation | After SDL_StopTextInput | After production fix |
| --- | --- | --- | --- |
| First decoder window | no HIMC | no HIMC | unchanged |
| Second stream window | HIMC present | HIMC present | no HIMC |
| Recreated stream window | HIMC present | HIMC present | no HIMC |

`SDL_IsTextInputActive()` reports false throughout. This reproduces a mismatch
between SDL's text-input state and the native streaming HWND's IME association.
The first window is kept alive to exclude HWND recycling from this result.

In [SDL 3.4.18's Windows keyboard implementation](https://github.com/libsdl-org/SDL/blob/release-3.4.18/src/video/windows/SDL_windowskeyboard.c),
`IME_Init()` initializes `ime_hwnd_main/current` once; later calls return early.
`IME_Disable()` disassociates that stored HWND rather than the `hwnd` argument.
Window creation calls `WIN_StopTextInput()`, so a decoder-probe window can
become the stored target. SDL's later `SDL_StopTextInput(window)` also skips
platform work when that window is already marked text-input-inactive.
Calling SDL_StopTextInput again after creating the stream is therefore insufficient.

This is a confirmed local-IME exclusion defect. The original repeated/missing
typing has not been recorded as a full Win32→SDL→network event trace, so the
defect alone is not proof of every symptom's cause. Classic SDL2's native IME
context can also remain associated when text input is stopped before creating
windows; its other Windows keyboard/TSF behavior differs from SDL3.

## Repair

* Enable [SDL_WINDOWS_RAW_KEYBOARD](https://wiki.libsdl.org/SDL3/SDL_HINT_WINDOWS_RAW_KEYBOARD)
  before video initialization, only for Windows sdl2-compat/SDL3. SDL3 then
  forwards physical make/break input instead of the normal WM_KEY path, where
  a client IME can consume or modify messages.
* Use [ImmAssociateContextEx](https://learn.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontextex)
  with a null context on the actual stream HWND at assignment, focus gain,
  fullscreen transitions and after decoder creation.
  Query the HWND each time because fullscreen transitions can replace it.
  This affects the SDL streaming window, not the Qt connection UI or the host.
* Correct the special JIS DBE events inside SDL3 before updating SDL's key
  state. Moonlight then sends the corrected physical down/up sequence.
  Repeat keydowns remain filtered; focus loss still releases held keys.

## Half/full-width toggle defect found after fix.4

The user confirmed that fix.4 repaired Japanese typing, but then reported that
Hankaku/Zenkaku no longer toggled the host IME. A native Raw Input capture on
the client recorded only that key while Moonlight was foreground:

| MakeCode | Flags | VKey | Message |
| --- | --- | --- | --- |
| 0x29 | 0 | 0xf3 (VK_DBE_SBCSCHAR) | WM_KEYUP |
| 0x29 | 0 | 0xf4 (VK_DBE_DBCSCHAR) | WM_KEYDOWN |
| 0x29 | 0 | 0xf4 (VK_DBE_DBCSCHAR) | WM_KEYUP |
| 0x29 | 0 | 0xf3 (VK_DBE_SBCSCHAR) | WM_KEYDOWN |

SDL3 3.4.18 derives direction solely from RI_KEY_BREAK. All four events above
therefore become keydowns: the key stays held, later events become repeats,
and Moonlight discards them. These DBE toggle messages use WM_KEYUP for the
physical press and WM_KEYDOWN for release, as the fork's earlier WM_KEY
workaround also handles.

`scripts/patches/sdl3-jis-toggle.patch` corrects only scan 0x29 with these two
DBE virtual keys. All other Raw Input keeps its original flags-based decoding.
The correction must happen before SDL's keyboard-state/repeat handling; merely
inverting Moonlight's final packet cannot restore an event already discarded.

`scripts/build-sdl3-jis.bat` builds SDL3 from release-3.4.18 commit
`829a65d769d935c4852f8159e964312c0957260a` with this patch. Dependency setup
uses it by default. `SDL3-jis-build.json` records the source revision, patch
hash and compiled DLL hash; this is an altered SDL3 build, not upstream's DLL.
SDL3 remains version 3.4.18 and sdl2-compat remains 2.32.74.

## Grabbed shortcut defect reported after fix.5

The user subsequently reported that combinations such as copy/paste did not
work. The earlier live fix.5 confirmation covered typing and IME toggling,
not keyboard-grab modifier delivery.

In SDL3 3.4.18, `WIN_KeyboardHookProc()` intercepts Ctrl, Alt, GUI, PrintScreen,
Tab and Escape and returns 1 to suppress normal Windows handling. However,
it sends the intercepted key to SDL only when `raw_keyboard_enabled` is false.
The swallowed transitions are also unavailable to the Raw Input path, so the
Raw Input configuration used by this fork loses modifiers while grabbed.
For example, C reaches Moonlight without a corresponding Ctrl press.

fix.6 extends the SDL3 patch so the hook forwards its intercepted transitions
in both input modes. Ordinary keys continue through Raw Input. The existing
AltGr fake-Ctrl exclusion and release of modifiers held before grabbing are
preserved. Japanese DBE direction correction and local IME exclusion remain.

`tests/run-grabbed-shortcuts.py` compiles the exact production hook with a
captured event sink and a Windows-routing model (suppressed input does not
also reach Raw Input). The unpatched hook fails for the expected missing Ctrl.
The patched hook passes repeated Ctrl+C/V/A/Z, nested left/right modifiers,
Shift combinations, reversed release order, Alt/GUI, AltGr and pre-grab release.
This test does not inject global keyboard input or prove end-to-end host
shortcut operation. On 2026-10-10, the user tested fix.6 with Ctrl+C/V, Ctrl+A,
Shift selection and Japanese input and confirmed that simultaneous shortcuts
and Japanese input were normal in the live Windows 11 client/host stream.
This qualifies that environment, not every keyboard, IME or system shortcut.

## Verification and limits

`tests/run-keyboard-regression.bat --reproduce-ime` passes locally against the
exact v19 DLLs. It executes the production Windows helper with native SDL
windows and checks Raw Input device registration, the before/after HIMC state,
WM_KEY suppression in Raw Input mode (and two events when it is disabled),
window recreation, legacy transport parity and Raw Input JIS key release.
It does not inject global input or interfere with an active stream.

`tests/run-jis-raw-decoder.py` compiles the exact patched decoder and replays
the captured events: 200 balanced presses/releases, repeated holds and ordinary
keys pass. This reproduces the decoder defect without recording text keys.

CI runs the same checks without requiring the original HIMC defect to exist
on the runner. Package checks verify source/patch provenance, both SDL DLL hashes and actual
Moonlight startup. These checks cannot substitute for user Japanese typing
through Sunshine, including conversion, missing characters and key repetition.
Remote Desktop, software keyboards and third-party injected input have not
been qualified with the Raw Input path.

fix.5 contains the DBE correction. On 2026-10-10, the user tested fix.5 on the
Windows 11 client/host and explicitly confirmed that both half/full-width
toggling and Japanese typing were normal. This is a live user confirmation,
not an automated Sunshine/IME test or validation of every keyboard/device.
The later shortcut report supersedes the designation of fix.5 as final.
fix.6 is the final release after live shortcut and typing confirmation;
v6.1 remains available. Source history and
`setup-deps.ps1 -UseClassicSdl` preserve the classic comparison option.
Other dependencies remain v19.
