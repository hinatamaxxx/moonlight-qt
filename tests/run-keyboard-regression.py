"""Compile and exercise the production keyboard handler with a captured transport.

Run from an MSVC x64 command prompt after setup-deps.ps1 and submodule checkout.
Qt UI/session code is omitted; SDL and Moonlight protocol definitions are real.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "app/streaming/input/keyboard.cpp").read_text()
definitions = source[source.index("#define VK_0"):source.index("void SdlInputHandler::performSpecialKeyCombo")]
handler = source[source.index("void SdlInputHandler::handleKeyEvent"):]

prefix = r'''
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <Limelight.h>
#include <windows.h>
#include <cassert>
#include <cstdio>
#include <set>
#include <vector>
#include <utility>
#define Q_FALLTHROUGH() [[fallthrough]]
#undef SDL_assert
#define SDL_assert(x) assert(x)
#define SDL_LogInfo(...) ((void)0)

static LANGID testLayout = 0x0411;
static HKL keyboardLayout(DWORD) { return reinterpret_cast<HKL>(static_cast<UINT_PTR>(testLayout)); }
#define GetKeyboardLayout keyboardLayout
#define GetForegroundWindow() nullptr
#define GetWindowThreadProcessId(window, process) 0

struct SentKey { short code; char action, modifiers, flags; };
static std::vector<SentKey> sent;
int LiSendKeyboardEvent2(short code, char action, char modifiers, char flags) {
    sent.push_back({code, action, modifiers, flags});
    return 0;
}
template<typename T> struct TestSet : std::set<T> {
    bool isEmpty() const { return this->empty(); }
    size_t count() const { return this->size(); }
    void remove(T value) { this->erase(value); }
};
class SdlInputHandler {
public:
    enum { KeyComboMax = 1 };
    struct Combo { bool enabled = false; SDL_Keycode keyCode = 0; SDL_Scancode scanCode = SDL_SCANCODE_UNKNOWN; int keyCombo = 0; };
    Combo m_SpecialKeyCombos[KeyComboMax];
    TestSet<uint32_t> m_KeysDown;
    bool isSystemKeyCaptureActive() { return true; }
    void performSpecialKeyCombo(int) {}
    void handleKeyEvent(SDL_KeyboardEvent* event);
    void raiseAllKeys();
};
'''

tests = r'''
static void input(SdlInputHandler& handler, SDL_Scancode code, Uint8 state, Uint8 repeat = 0, Uint16 mod = 0) {
    SDL_KeyboardEvent event{};
    event.state = state;
    event.repeat = repeat;
    event.keysym.scancode = code;
    event.keysym.mod = mod;
    handler.handleKeyEvent(&event);
}
static void expectKey(size_t index, int code, char action, char flags = 0, char modifiers = 0) {
    assert(index < sent.size());
    assert(static_cast<unsigned short>(sent[index].code) == (0x8000 | code));
    assert(sent[index].action == action);
    assert(sent[index].flags == flags);
    assert(sent[index].modifiers == modifiers);
}
int main() {
    // Reversed Windows JIS toggle sequence must finish with no held key.
    SdlInputHandler jis;
    input(jis, SDL_SCANCODE_GRAVE, SDL_RELEASED);
    input(jis, SDL_SCANCODE_GRAVE, SDL_PRESSED);
#ifdef Q_OS_WIN
    expectKey(0, 0xC0, KEY_ACTION_DOWN);
    expectKey(1, 0xC0, KEY_ACTION_UP);
#else
    expectKey(0, 0xC0, KEY_ACTION_UP);
    expectKey(1, 0xC0, KEY_ACTION_DOWN);
    jis.raiseAllKeys();
#endif
    assert(jis.m_KeysDown.empty());
    sent.clear();

    // Focus loss must release a corrected JIS press through v6.2.0 tracking.
#ifdef Q_OS_WIN
    input(jis, SDL_SCANCODE_GRAVE, SDL_RELEASED);
    assert(jis.m_KeysDown.size() == 1);
    jis.raiseAllKeys();
    expectKey(1, 0xC0, KEY_ACTION_UP);
    assert(jis.m_KeysDown.empty());
    sent.clear();
#endif

    // US backtick remains a normal down/up pair even on Windows.
    testLayout = 0x0409;
    input(jis, SDL_SCANCODE_GRAVE, SDL_PRESSED);
    input(jis, SDL_SCANCODE_GRAVE, SDL_RELEASED);
    expectKey(0, 0xC0, KEY_ACTION_DOWN);
    expectKey(1, 0xC0, KEY_ACTION_UP);
    assert(jis.m_KeysDown.empty());
    sent.clear();
    testLayout = 0x0411;

    // Test many toggles and normal text interleaved without lingering keys.
    for (int i = 0; i < 50; ++i) {
        input(jis, SDL_SCANCODE_GRAVE, SDL_RELEASED);
        input(jis, SDL_SCANCODE_GRAVE, SDL_PRESSED);
        input(jis, SDL_SCANCODE_A, SDL_PRESSED);
        input(jis, SDL_SCANCODE_A, SDL_PRESSED, 1);
        input(jis, SDL_SCANCODE_A, SDL_RELEASED);
#ifndef Q_OS_WIN
        jis.raiseAllKeys();
#endif
        assert(jis.m_KeysDown.empty());
    }
#ifdef Q_OS_WIN
    assert(sent.size() == 200);
#endif
    sent.clear();

    // JIS yen, ro/underscore, and legacy ISO mapping retain protocol flags.
    const SDL_Scancode special[] = {SDL_SCANCODE_INTERNATIONAL3, SDL_SCANCODE_INTERNATIONAL1, SDL_SCANCODE_NONUSBACKSLASH};
    for (auto scan : special) {
        input(jis, scan, SDL_PRESSED, 0, KMOD_SHIFT);
        jis.raiseAllKeys();
        int vk = scan == SDL_SCANCODE_INTERNATIONAL3 ? 0xDC : 0xE2;
        expectKey(0, vk, KEY_ACTION_DOWN, SS_KBE_FLAG_NON_NORMALIZED, MODIFIER_SHIFT);
        expectKey(1, vk, KEY_ACTION_UP, SS_KBE_FLAG_NON_NORMALIZED);
        assert(jis.m_KeysDown.empty());
        sent.clear();
    }

    // Upstream extended keys and conversion mappings must still work.
    input(jis, SDL_SCANCODE_RCTRL, SDL_PRESSED);
    jis.raiseAllKeys();
    expectKey(0, 0xA3, KEY_ACTION_DOWN, 0, MODIFIER_EXTENDED);
    expectKey(1, 0xA3, KEY_ACTION_UP, 0, MODIFIER_EXTENDED);
    sent.clear();
    input(jis, SDL_SCANCODE_LANG1, SDL_PRESSED);
    input(jis, SDL_SCANCODE_LANG1, SDL_RELEASED);
    input(jis, SDL_SCANCODE_LANG2, SDL_PRESSED);
    input(jis, SDL_SCANCODE_LANG2, SDL_RELEASED);
    expectKey(0, 0x1C, KEY_ACTION_DOWN);
    expectKey(1, 0x1C, KEY_ACTION_UP);
    expectKey(2, 0x1D, KEY_ACTION_DOWN);
    expectKey(3, 0x1D, KEY_ACTION_UP);
    assert(jis.m_KeysDown.empty());
    sent.clear();
    jis.raiseAllKeys();
    assert(sent.empty());
    puts("Keyboard regression checks passed (captured transport; no live IME host).");
}
'''

with tempfile.TemporaryDirectory(prefix="moonlight-keyboard-") as temp:
    build = Path(temp)
    cpp = build / "keyboard-regression.cpp"
    cpp.write_text(prefix + definitions + handler + tests)
    includes = [root / "libs/windows/include/x64/SDL2", root / "moonlight-common-c/moonlight-common-c/src"]
    for mode in ("windows-jis", "upstream-platform"):
        exe = build / f"{mode}.exe"
        command = ["cl", "/nologo", "/std:c++17", "/EHsc", "/W3"]
        command += [f"/I{path}" for path in includes]
        if mode == "windows-jis":
            command += ["/DQ_OS_WIN"]
        command += [str(cpp), f"/Fe:{exe}"]
        subprocess.run(command, cwd=build, check=True)
        subprocess.run([str(exe)], check=True)
