"""Verify the packaged SDL runtime and launch the real Moonlight executable."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIN = json.loads((ROOT / 'scripts/classic-sdl.json').read_text(encoding='utf-8'))

def verify_runtime(directory):
    dll = directory / 'SDL2.dll'
    assert hashlib.sha256(dll.read_bytes()).hexdigest() == PIN['dllSha256']
    pe = dll.read_bytes()
    offset = struct.unpack_from('<I', pe, 0x3c)[0]
    assert pe[offset:offset + 4] == b'PE\0\0'
    assert struct.unpack_from('<H', pe, offset + 4)[0] == 0x8664

    class Version(ctypes.Structure):
        _fields_ = [('major', ctypes.c_uint8), ('minor', ctypes.c_uint8), ('patch', ctypes.c_uint8)]

    with os.add_dll_directory(str(directory)):
        sdl = ctypes.CDLL(str(dll))
        sdl.SDL_GetError.restype = ctypes.c_char_p
        version = Version()
        sdl.SDL_GetVersion(ctypes.byref(version))
        actual = f'{version.major}.{version.minor}.{version.patch}'
        assert actual == PIN['version'], actual
        assert sdl.SDL_Init(0x20) == 0, sdl.SDL_GetError()
        try:
            sdl.SDL_StopTextInput()
            sdl.SDL_CreateWindow.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
            sdl.SDL_CreateWindow.restype = ctypes.c_void_p
            sdl.SDL_DestroyWindow.argtypes = [ctypes.c_void_p]
            window = sdl.SDL_CreateWindow(b'Moonlight SDL compatibility test', 0, 0, 320, 240, 8)
            assert window, sdl.SDL_GetError()
            try:
                assert sdl.SDL_IsTextInputActive() == 0
                ttf = ctypes.CDLL(str(directory / 'SDL2_ttf.dll'))
                assert ttf.TTF_Init() == 0, sdl.SDL_GetError()
                ttf.TTF_Quit()
            finally:
                sdl.SDL_DestroyWindow(window)
        finally:
            sdl.SDL_Quit()

    app = subprocess.run([str(directory / 'Moonlight.exe'), '--help'], cwd=directory,
                         capture_output=True, timeout=30)
    assert app.returncode == 0, app.returncode
    assert b'Available actions:' in app.stdout, 'Moonlight startup/help failed'
    print(f'Classic SDL {actual}: pinned hash, x64, hidden window, SDL_ttf and Moonlight startup passed.')

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--package', type=Path)
    group.add_argument('--runtime-dir', type=Path)
    args = parser.parse_args()
    if args.runtime_dir:
        verify_runtime(args.runtime_dir.resolve())
        return
    with tempfile.TemporaryDirectory(prefix='moonlight-classic-sdl-') as temp:
        destination = Path(temp).resolve()
        with zipfile.ZipFile(args.package) as archive:
            assert archive.testzip() is None
            names = archive.namelist()
            for required in ('Moonlight.exe', 'SDL2.dll', 'SDL2_ttf.dll', 'portable.dat', 'platforms/qwindows.dll'):
                assert required in names, required
            for name in names:
                assert (destination / name).resolve().is_relative_to(destination), name
                assert not name.lower().endswith(('.ini', '.log')), 'Private runtime state in release archive'
            archive.extractall(destination)
        # DLLs stay loaded until worker exit; keep Windows temp cleanup in parent.
        subprocess.run([sys.executable, str(Path(__file__).resolve()), '--runtime-dir', str(destination)], check=True)

if __name__ == '__main__':
    main()
