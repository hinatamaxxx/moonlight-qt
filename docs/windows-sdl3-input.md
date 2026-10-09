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
  with a null context on the actual stream HWND at assignment and focus gain.
  Query the HWND each time because fullscreen transitions can replace it.
  This affects the SDL streaming window, not the Qt connection UI or the host.
* In Raw Input mode, send Hankaku/Zenkaku in physical down/up order. Do not
  apply the legacy reversed-WM_KEY workaround to an already physical sequence.
  Repeat keydowns remain filtered; focus loss still releases held keys.

## Verification and limits

`tests/run-keyboard-regression.bat --reproduce-ime` passes locally against the
exact v19 DLLs. It executes the production Windows helper with native SDL
windows and checks Raw Input device registration, the before/after HIMC state,
WM_KEY suppression in Raw Input mode (and two events when it is disabled),
window recreation, legacy transport parity and Raw Input JIS key release.
It does not inject global input or interfere with an active stream.

CI runs the same checks without requiring the original HIMC defect to exist
on the runner. Package checks pin both SDL DLL hashes and verify actual
Moonlight startup. These checks cannot substitute for user Japanese typing
through Sunshine, including conversion, missing characters and key repetition.
Remote Desktop, software keyboards and third-party injected input have not
been qualified with the Raw Input path.

Use fix.3 or `setup-deps.ps1 -UseClassicSdl` as a comparison/fallback until
live typing with the SDL3 build is confirmed. Other dependencies remain v19.
