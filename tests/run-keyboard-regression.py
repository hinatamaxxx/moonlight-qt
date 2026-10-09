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
static bool rawInput = false;
namespace WindowsKeyboardInput {
    static bool usesRawInput() { return rawInput; }
}
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

legacy = (root / "tests/fixtures/keyboard-v6.1.0.cpp").read_text()
legacy = legacy[legacy.index("void SdlInputHandler::handleKeyEvent"):].replace("SdlInputHandler::", "LegacyInputHandler::")
legacy_class = prefix[prefix.index("class SdlInputHandler"):].replace("SdlInputHandler", "LegacyInputHandler").replace("TestSet<uint32_t>", "TestSet<short>")
legacy += r"""
void LegacyInputHandler::raiseAllKeys() {
    for (auto key : m_KeysDown) LiSendKeyboardEvent2(0x8000 | key, KEY_ACTION_UP, 0, 0);
    m_KeysDown.clear();
}
"""

tests = r'''
static void compareInput(SdlInputHandler& current, LegacyInputHandler& old,
                         SDL_Scancode scan, Uint8 state, Uint16 mod, Uint8 repeat = 0) {
    SDL_KeyboardEvent event{};
    event.state = state;
    event.repeat = repeat;
    event.keysym.scancode = scan;
    event.keysym.mod = mod;
    sent.clear();
    old.handleKeyEvent(&event);
    auto expected = sent;
    sent.clear();
    current.handleKeyEvent(&event);
    assert(sent.size() == expected.size());
    for (size_t i = 0; i < sent.size(); ++i) {
        assert(sent[i].code == expected[i].code);
        assert(sent[i].action == expected[i].action);
        assert(sent[i].modifiers == expected[i].modifiers);
        assert(sent[i].flags == expected[i].flags);
    }
    std::set<short> held;
    for (auto key : current.m_KeysDown) held.insert(GET_KEYPRESS_CODE(key) & 0x7FFF);
    assert(held == static_cast<const std::set<short>&>(old.m_KeysDown));
}
int main() {
    // Differential oracle: unmodified handler from fork commit c13f4a21507b.
    const Uint16 mods[] = {0, KMOD_SHIFT, KMOD_CTRL, KMOD_ALT, KMOD_GUI,
                          KMOD_CTRL | KMOD_ALT | KMOD_SHIFT};
    for (auto mod : mods) {
        for (int scan = 0; scan < SDL_NUM_SCANCODES; ++scan) {
            SdlInputHandler current;
            LegacyInputHandler old;
            compareInput(current, old, static_cast<SDL_Scancode>(scan), SDL_PRESSED, mod);
            compareInput(current, old, static_cast<SDL_Scancode>(scan), SDL_PRESSED, mod, 1);
            compareInput(current, old, static_cast<SDL_Scancode>(scan), SDL_RELEASED, mod);
            compareInput(current, old, static_cast<SDL_Scancode>(scan), SDL_PRESSED, 0);
        }
    }
    // Corrected JIS sequences and interleaved text leave no stuck keys.
    SdlInputHandler current;
    LegacyInputHandler old;
    for (int i = 0; i < 50; ++i) {
        compareInput(current, old, SDL_SCANCODE_GRAVE, SDL_RELEASED, 0);
        compareInput(current, old, SDL_SCANCODE_GRAVE, SDL_PRESSED, 0);
        compareInput(current, old, SDL_SCANCODE_A, SDL_PRESSED, 0);
        compareInput(current, old, SDL_SCANCODE_A, SDL_RELEASED, 0);
        assert(current.m_KeysDown.empty());
    }
    // v6.2.0 focus-loss release must retain the code and flags of each press.
    const SDL_Scancode keys[] = {SDL_SCANCODE_GRAVE, SDL_SCANCODE_A,
        SDL_SCANCODE_INTERNATIONAL1, SDL_SCANCODE_INTERNATIONAL3,
        SDL_SCANCODE_NONUSBACKSLASH, SDL_SCANCODE_RCTRL};
    for (auto scan : keys) {
        SDL_KeyboardEvent event{};
        event.keysym.scancode = scan;
        event.state = scan == SDL_SCANCODE_GRAVE ? SDL_RELEASED : SDL_PRESSED;
        sent.clear();
        current.handleKeyEvent(&event);
        assert(sent.size() == 1);
        auto down = sent[0];
        assert(down.action == KEY_ACTION_DOWN);
        current.raiseAllKeys();
        assert(sent.size() == 2);
        assert(sent[1].code == down.code);
        assert(sent[1].flags == down.flags);
        assert(sent[1].action == KEY_ACTION_UP);
        assert(current.m_KeysDown.empty());
    }
    puts("Legacy parity: all SDL scancodes, modifiers, repeats and JIS sequences passed.");
    puts("v6.2.0 focus-loss key release passed (captured transport; no live IME host).");

    // Raw Input already has physical press/release order. It must not use
    // the old WM_KEY/IME Hankaku-Zenkaku inversion.
    rawInput = true;
    const SDL_Scancode rawKeys[] = {SDL_SCANCODE_GRAVE, SDL_SCANCODE_A,
        SDL_SCANCODE_INTERNATIONAL1, SDL_SCANCODE_INTERNATIONAL3,
        SDL_SCANCODE_NONUSBACKSLASH, SDL_SCANCODE_RCTRL};
    for (auto scan : rawKeys) {
        SdlInputHandler raw;
        SDL_KeyboardEvent event{};
        event.keysym.scancode = scan;
        event.state = SDL_PRESSED;
        sent.clear();
        raw.handleKeyEvent(&event);
        assert(sent.size() == 1 && sent[0].action == KEY_ACTION_DOWN);
        auto down = sent[0];
        event.repeat = 1;
        raw.handleKeyEvent(&event);
        assert(sent.size() == 1);
        event.repeat = 0;
        event.state = SDL_RELEASED;
        raw.handleKeyEvent(&event);
        assert(sent.size() == 2 && sent[1].action == KEY_ACTION_UP);
        assert(sent[1].code == down.code && sent[1].flags == down.flags);
        assert(raw.m_KeysDown.empty());
        event.state = SDL_PRESSED;
        raw.handleKeyEvent(&event);
        raw.raiseAllKeys();
        assert(sent.back().action == KEY_ACTION_UP && raw.m_KeysDown.empty());
    }
    puts("Raw Input JIS press/release, repeat filtering and focus-loss release passed.");
}
'''

with tempfile.TemporaryDirectory(prefix="moonlight-keyboard-") as temp:
    build = Path(temp)
    cpp = build / "keyboard-regression.cpp"
    cpp.write_text(prefix + definitions + handler + legacy_class + legacy + tests)
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
