#define SDL_MAIN_HANDLED
#define Q_OS_WIN32
#include "streaming/input/windowskeyboard.h"
#include <cassert>
#include <cstdio>
#include <vector>
#include <cstring>

static HWND nativeWindow(SDL_Window* window)
{
    SDL_SysWMinfo info = {};
    SDL_VERSION(&info.version);
    assert(SDL_GetWindowWMInfo(window, &info));
    assert(info.subsystem == SDL_SYSWM_WINDOWS);
    return info.info.win.window;
}

static bool hasIme(SDL_Window* window)
{
    HWND hwnd = nativeWindow(window);
    HIMC context = ImmGetContext(hwnd);
    if (context) ImmReleaseContext(hwnd, context);
    return context != nullptr;
}

static int keyboardEvents()
{
    int count = 0;
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_KEYDOWN || event.type == SDL_KEYUP) ++count;
    }
    return count;
}

int main(int argc, char** argv)
{
    bool reproduce = argc > 1 && strcmp(argv[1], "--reproduce-ime") == 0;
    assert(WindowsKeyboardInput::usesSdl3Backend());
    WindowsKeyboardInput::configure();
    assert(WindowsKeyboardInput::usesRawInput());
    SDL_SetMainReady();
    assert(SDL_Init(SDL_INIT_VIDEO) == 0);
    SDL_StopTextInput();

    UINT deviceCount = 0;
    assert(GetRegisteredRawInputDevices(nullptr, &deviceCount, sizeof(RAWINPUTDEVICE)) == 0);
    std::vector<RAWINPUTDEVICE> devices(deviceCount);
    assert(GetRegisteredRawInputDevices(devices.data(), &deviceCount, sizeof(RAWINPUTDEVICE)) != UINT(-1));
    bool keyboardRegistered = false;
    for (const auto& device : devices) {
        if (device.usUsagePage == 1 && device.usUsage == 6) keyboardRegistered = true;
    }
    assert(keyboardRegistered);

    // Match Session::initialize(): disable text, create decoder probe, then
    // streaming window. Keep the probe alive to rule out recycled HWNDs.
    SDL_Window* probe = SDL_CreateWindow("decoder probe", 0, 0, 64, 64, SDL_WINDOW_HIDDEN);
    assert(probe);
    SDL_Window* stream = SDL_CreateWindow("stream", 0, 0, 64, 64, SDL_WINDOW_HIDDEN);
    assert(stream);
    SDL_StopTextInput();
    if (reproduce) {
        assert(!hasIme(probe));
        assert(hasIme(stream));
        puts("Reproduced: SDL text input is inactive but second HWND retains an IME context.");
    }
    assert(!SDL_IsTextInputActive());
    WindowsKeyboardInput::disableLocalIme(stream);
    assert(!hasIme(stream));
    WindowsKeyboardInput::disableLocalIme(stream);
    assert(!hasIme(stream));

    // WM_KEY must not provide a second copy of physical keyboard input.
    keyboardEvents();
    HWND hwnd = nativeWindow(stream);
    SendMessageW(hwnd, WM_KEYDOWN, 'A', 1 | (0x1e << 16));
    SendMessageW(hwnd, WM_KEYUP, 'A', 1 | (0x1e << 16) | LPARAM(0xc0000000));
    assert(keyboardEvents() == 0);
    SDL_SetHint("SDL_WINDOWS_RAW_KEYBOARD", "0");
    SendMessageW(hwnd, WM_KEYDOWN, 'A', 1 | (0x1e << 16));
    SendMessageW(hwnd, WM_KEYUP, 'A', 1 | (0x1e << 16) | LPARAM(0xc0000000));
    assert(keyboardEvents() == 2);
    WindowsKeyboardInput::configure();
    assert(WindowsKeyboardInput::usesRawInput());

    SDL_DestroyWindow(stream);
    stream = SDL_CreateWindow("recreated stream", 0, 0, 64, 64, SDL_WINDOW_HIDDEN);
    assert(stream);
    WindowsKeyboardInput::disableLocalIme(stream);
    assert(!hasIme(stream));
    SDL_DestroyWindow(stream);
    SDL_DestroyWindow(probe);
    SDL_Quit();
    puts("SDL3 Raw Input registration, IME exclusion, WM_KEY deduplication and window recreation passed.");
}
