#pragma once

#include "SDL_compat.h"

#ifdef Q_OS_WIN32
#include <SDL_syswm.h>
#include <imm.h>
#endif

namespace WindowsKeyboardInput {

inline bool usesSdl3Backend()
{
#ifdef Q_OS_WIN32
    SDL_version version;
    SDL_GetVersion(&version);
    return SDL_GetHint("SDL3_VERSION") ||
            (version.major == 2 && version.minor >= 30 && version.patch >= 50);
#else
    return false;
#endif
}

inline void configure()
{
#ifdef Q_OS_WIN32
    if (usesSdl3Backend()) {
        // Forward physical make/break events to the host. WM_KEY messages can
        // be consumed or rewritten by the client's IME before SDL sees them.
        SDL_SetHint("SDL_WINDOWS_RAW_KEYBOARD", "1");
    }
#endif
}

inline bool usesRawInput()
{
    return usesSdl3Backend() && SDL_GetHintBoolean("SDL_WINDOWS_RAW_KEYBOARD", SDL_FALSE);
}

inline void disableLocalIme(SDL_Window* window)
{
#ifdef Q_OS_WIN32
    if (!window || !usesSdl3Backend()) {
        return;
    }

    SDL_SysWMinfo info = {};
    SDL_VERSION(&info.version);
    if (!SDL_GetWindowWMInfo(window, &info) || info.subsystem != SDL_SYSWM_WINDOWS) {
        SDL_LogWarn(SDL_LOG_CATEGORY_INPUT, "Unable to get streaming HWND: %s", SDL_GetError());
        return;
    }

    // SDL 3.4.18 initializes IMM against the first (decoder test) window.
    // Later windows can retain an HIMC even after SDL_StopTextInput(). The
    // stream transports keys; composition belongs exclusively to the host.
    if (!ImmAssociateContextEx(info.info.win.window, nullptr, 0)) {
        SDL_LogWarn(SDL_LOG_CATEGORY_INPUT, "Unable to disable local streaming IME: %lu", GetLastError());
    }
#else
    (void)window;
#endif
}

}
