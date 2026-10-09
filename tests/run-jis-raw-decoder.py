"""Exercise the exact patched SDL3 decoder with captured Windows JIS events."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--sdl3-source', type=Path, default=Path(os.environ['LOCALAPPDATA']) / 'Moonlight-SDL3-JIS/source')
args = parser.parse_args()
text = (args.sdl3_source / 'src/video/windows/SDL_windowsevents.c').read_text()
decoder = text[text.index('static bool WIN_RawKeyboardIsKeyDown('):
               text.index('static void WIN_HandleRawKeyboardInput(')]
test = r'''
#include <windows.h>
#include <cassert>
#include <cstdio>
DECODER
int main() {
    // Client capture: every Flags value is zero, even physical releases.
    const RAWKEYBOARD captured[] = {
        {0x29, 0, 0, 0xf3, WM_KEYUP, 0},
        {0x29, 0, 0, 0xf4, WM_KEYDOWN, 0},
        {0x29, 0, 0, 0xf4, WM_KEYUP, 0},
        {0x29, 0, 0, 0xf3, WM_KEYDOWN, 0},
    };
    bool held = false;
    int presses = 0, releases = 0;
    for (int cycle = 0; cycle < 100; ++cycle) {
        for (int i = 0; i < 4; ++i) {
            const auto& key = captured[i];
            bool down = WIN_RawKeyboardIsKeyDown(&key);
            assert(down == (i % 2 == 0));
            assert(down != held);
            held = down;
            if (down) {
                ++presses;
                // Repeated DBE messages decode as held; SDL filters repeats.
                for (int repeat = 0; repeat < 10; ++repeat) {
                    assert(WIN_RawKeyboardIsKeyDown(&key) && held);
                }
            } else ++releases;
        }
        assert(!held);
    }
    assert(presses == 200 && releases == 200);
    RAWKEYBOARD normal = {0x29, 0, 0, VK_OEM_3, WM_KEYDOWN, 0};
    assert(WIN_RawKeyboardIsKeyDown(&normal));
    normal.Flags = RI_KEY_BREAK;
    normal.Message = WM_KEYUP;
    assert(!WIN_RawKeyboardIsKeyDown(&normal));
    normal.MakeCode = 0x1e;
    normal.VKey = 'A';
    assert(!WIN_RawKeyboardIsKeyDown(&normal));
    normal.Flags = 0;
    assert(WIN_RawKeyboardIsKeyDown(&normal));
    puts("Captured JIS raw events: 200 balanced presses/releases, repeats and ordinary keys passed.");
}
'''.replace('DECODER', decoder)
with tempfile.TemporaryDirectory(prefix='moonlight-jis-decoder-') as temp:
    build = Path(temp)
    cpp = build / 'jis-raw-decoder.cpp'
    cpp.write_text(test)
    exe = build / 'jis-raw-decoder.exe'
    subprocess.run(['cl', '/nologo', '/std:c++17', '/EHsc', '/W3', str(cpp), f'/Fe:{exe}'],
                   cwd=build, check=True)
    subprocess.run([str(exe)], check=True)
