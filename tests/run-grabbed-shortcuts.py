"""Compile the exact SDL3 grab hook and test intercepted/raw key sequences.

The transport models Windows delivering Raw Input only for hook return 0.
This is a callback regression test; it does not inject global keyboard input.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--sdl3-source', type=Path,
                    default=Path(os.environ['LOCALAPPDATA']) / 'Moonlight-SDL3-JIS/source')
args = parser.parse_args()
source = (args.sdl3_source / 'src/video/windows/SDL_windowsevents.c').read_text()
hook = source[source.index('LRESULT CALLBACK\nWIN_KeyboardHookProc('):
              source.index('static bool WIN_SwapButtons(')]
prefix = r'''
#define SDL_MAIN_HANDLED
#include <windows.h>
#include <SDL.h>
#include <cassert>
#include <cstdio>
#include <vector>
#include <array>
#include <utility>
using SDL_KeyboardID = unsigned;
constexpr SDL_KeyboardID SDL_GLOBAL_KEYBOARD_ID = 0;
struct SDL_VideoData { bool raw_keyboard_enabled; BYTE pre_hook_key_state[256]{}; };
struct Video { SDL_VideoData* internal; };
static SDL_VideoData videoData{};
static Video video{&videoData};
static Video* SDL_GetVideoDevice() { return &video; }
static LRESULT nextHook(HHOOK, int, WPARAM, LPARAM) { return 0; }
#define CallNextHookEx nextHook
struct Key { SDL_Scancode scan; bool down; Uint16 mods; };
static std::vector<Key> events;
static std::array<bool, SDL_NUM_SCANCODES> held{};
static Uint16 mods;
static Uint16 modifier(SDL_Scancode scan) {
    switch (scan) {
    case SDL_SCANCODE_LCTRL: return KMOD_LCTRL;
    case SDL_SCANCODE_RCTRL: return KMOD_RCTRL;
    case SDL_SCANCODE_LSHIFT: return KMOD_LSHIFT;
    case SDL_SCANCODE_RSHIFT: return KMOD_RSHIFT;
    case SDL_SCANCODE_LALT: return KMOD_LALT;
    case SDL_SCANCODE_RALT: return KMOD_RALT;
    case SDL_SCANCODE_LGUI: return KMOD_LGUI;
    case SDL_SCANCODE_RGUI: return KMOD_RGUI;
    default: return 0;
    }
}
static bool SDL_SendKeyboardKey(Uint64, SDL_KeyboardID, int, SDL_Scancode scan, bool down) {
    if (held[scan] == down) return false; // Ignore repeats / duplicate releases.
    held[scan] = down;
    if (down) mods |= modifier(scan); else mods &= ~modifier(scan);
    events.push_back({scan, down, mods});
    return true;
}
'''
tests = r'''
static void key(DWORD vk, DWORD rawScan, SDL_Scancode scan, bool down, bool system = false) {
    KBDLLHOOKSTRUCT data{};
    data.vkCode = vk;
    data.scanCode = rawScan;
    data.flags = down ? 0 : LLKHF_UP;
    WPARAM message = system ? (down ? WM_SYSKEYDOWN : WM_SYSKEYUP) : (down ? WM_KEYDOWN : WM_KEYUP);
    LRESULT intercepted = WIN_KeyboardHookProc(HC_ACTION, message, reinterpret_cast<LPARAM>(&data));
    if (!intercepted) SDL_SendKeyboardKey(0, 1, rawScan, scan, down);
}
static void reset(bool raw) {
    videoData = {};
    videoData.raw_keyboard_enabled = raw;
    held.fill(false);
    mods = 0;
    events.clear();
}
int main() {
    reset(true);
    key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, true);
    if (events.empty()) {
        puts("Reproduced defect: grabbed Ctrl is swallowed while Raw Input is enabled.");
        return 2;
    }
    for (bool raw : {false, true}) {
        for (int cycle = 0; cycle < 100; ++cycle) {
            for (auto letterKey : {std::pair<DWORD, SDL_Scancode>{'C', SDL_SCANCODE_C},
                                  {'V', SDL_SCANCODE_V}, {'A', SDL_SCANCODE_A}, {'Z', SDL_SCANCODE_Z}}) {
                SDL_Scancode letter = letterKey.second;
                reset(raw);
                key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, true);
                key(letterKey.first, 0x2e, letter, true);
                assert(events.size() == 2);
                assert(events[0].scan == SDL_SCANCODE_LCTRL && events[0].down);
                assert(events[1].scan == letter && (events[1].mods & KMOD_LCTRL));
                key(letterKey.first, 0x2e, letter, false);
                key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, false);
                assert(events.size() == 4 && mods == 0);
                // Fast re-press and release the modifier before the letter.
                key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, true);
                key(letterKey.first, 0x2e, letter, true);
                key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, false);
                key(letterKey.first, 0x2e, letter, false);
                assert(events.size() == 8 && mods == 0);
                assert(!held[letter] && !held[SDL_SCANCODE_LCTRL]);
            }
        }
        reset(raw);
        key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, true);
        key(VK_RCONTROL, 0x1d, SDL_SCANCODE_RCTRL, true);
        key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, false);
        assert(mods == KMOD_RCTRL);
        key(VK_LSHIFT, 0x2a, SDL_SCANCODE_LSHIFT, true);
        key('C', 0x2e, SDL_SCANCODE_C, true);
        assert((events.back().mods & (KMOD_RCTRL | KMOD_LSHIFT)) == (KMOD_RCTRL | KMOD_LSHIFT));
        key('C', 0x2e, SDL_SCANCODE_C, false);
        key(VK_LSHIFT, 0x2a, SDL_SCANCODE_LSHIFT, false);
        key(VK_RCONTROL, 0x1d, SDL_SCANCODE_RCTRL, false);
        assert(mods == 0);
        for (auto pair : {std::pair<DWORD, SDL_Scancode>{VK_LMENU, SDL_SCANCODE_LALT},
                           {VK_RMENU, SDL_SCANCODE_RALT}, {VK_LWIN, SDL_SCANCODE_LGUI},
                           {VK_RWIN, SDL_SCANCODE_RGUI}, {VK_SNAPSHOT, SDL_SCANCODE_PRINTSCREEN},
                           {VK_TAB, SDL_SCANCODE_TAB}, {VK_ESCAPE, SDL_SCANCODE_ESCAPE}}) {
            reset(raw);
            key(pair.first, 1, pair.second, true, true);
            key(pair.first, 1, pair.second, false, true);
            assert(events.size() == 2 && events[0].down && !events[1].down && mods == 0);
        }
        reset(raw);
        // Preserve AltGr's fake Ctrl filtering.
        key(VK_LCONTROL, 0x21d, SDL_SCANCODE_LCTRL, true);
        key(VK_LCONTROL, 0x21d, SDL_SCANCODE_LCTRL, false);
        assert(events.empty() && mods == 0);
        // A modifier held before grabbing must release both locally and in SDL.
        key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, true);
        videoData.pre_hook_key_state[VK_LCONTROL] = 0x80;
        key(VK_LCONTROL, 0x1d, SDL_SCANCODE_LCTRL, false);
        assert(events.size() == 2 && !held[SDL_SCANCODE_LCTRL] && mods == 0);
    }
    puts("Exact SDL3 grab hook: Ctrl+C/V/A/Z, modifier overlap, early release, Alt/GUI, AltGr and pre-grab release passed.");
}
'''
with tempfile.TemporaryDirectory(prefix='moonlight-grabbed-shortcuts-') as temp:
    build = Path(temp)
    cpp = build / 'grabbed-shortcuts.cpp'
    cpp.write_text(prefix + hook + tests)
    exe = build / 'grabbed-shortcuts.exe'
    subprocess.run(['cl', '/nologo', '/std:c++17', '/EHsc', '/W3',
                    f'/I{root / "libs/windows/include/x64/SDL2"}', str(cpp), f'/Fe:{exe}'],
                   cwd=build, check=True)
    subprocess.run([str(exe)], check=True)
