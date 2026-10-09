"""Exercise the production Windows helper with real sdl2-compat/SDL3 DLLs.

Run inside an MSVC x64 developer command prompt. No global input is injected.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--runtime-dir', type=Path, default=root / 'libs/windows/lib/x64')
parser.add_argument('--reproduce-ime', action='store_true')
args = parser.parse_args()

with tempfile.TemporaryDirectory(prefix='moonlight-sdl3-input-') as temp:
    build = Path(temp)
    exe = build / 'windows-input-runtime.exe'
    command = ['cl', '/nologo', '/std:c++17', '/EHsc', '/W3',
               f'/I{root / "app"}', f'/I{root / "libs/windows/include/x64/SDL2"}',
               str(root / 'tests/windows-keyboard-runtime.cpp'), f'/Fe:{exe}',
               '/link', f'/LIBPATH:{root / "libs/windows/lib/x64"}',
               'SDL2.lib', 'user32.lib', 'imm32.lib']
    subprocess.run(command, cwd=build, check=True)
    for filename in ('SDL2.dll', 'SDL3.dll'):
        shutil.copy2(args.runtime_dir / filename, build / filename)
    subprocess.run([str(exe)] + (['--reproduce-ime'] if args.reproduce_ime else []),
                   cwd=build, check=True, timeout=30)
