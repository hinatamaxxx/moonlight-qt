"""Verify the SDL3 release archive and start its actual Moonlight executable."""
import argparse
import ctypes as C
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zipfile

RUNTIMES = {
    'SDL2.dll': 'b5064d6a4c4826419ff2a5e271bf17be4e33f82d1ed59f7191cf358fe5bfcda0',
    'SDL3.dll': 'adb5717f9159c68f48ee7fed86d5d744eca0857b3a20a085794d193cf4335ae8',
}

def verify_runtime(directory):
    for name, expected in RUNTIMES.items():
        data = (directory / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, name
        offset = struct.unpack_from('<I', data, 0x3c)[0]
        assert data[offset:offset + 4] == b'PE\0\0'
        assert struct.unpack_from('<H', data, offset + 4)[0] == 0x8664

    class Version(C.Structure):
        _fields_ = [('major', C.c_uint8), ('minor', C.c_uint8), ('patch', C.c_uint8)]

    # sdl2-compat loads SDL3 with LoadLibraryA, which also searches the CWD.
    os.chdir(directory)
    with os.add_dll_directory(str(directory)):
        sdl = C.CDLL(str(directory / 'SDL2.dll'))
        sdl3 = C.CDLL(str(directory / 'SDL3.dll'))
        version = Version()
        sdl.SDL_GetVersion(C.byref(version))
        assert (version.major, version.minor, version.patch) == (2, 32, 74)
        assert sdl3.SDL_GetVersion() == 3004018
        sdl.SDL_SetHint.argtypes = [C.c_char_p, C.c_char_p]
        assert sdl.SDL_SetHint(b'SDL_WINDOWS_RAW_KEYBOARD', b'1')
        assert sdl.SDL_Init(0x20) == 0
        sdl.SDL_StopTextInput()
        sdl.SDL_CreateWindow.argtypes = [C.c_char_p, C.c_int, C.c_int, C.c_int, C.c_int, C.c_uint32]
        sdl.SDL_CreateWindow.restype = C.c_void_p
        sdl.SDL_DestroyWindow.argtypes = [C.c_void_p]
        window = sdl.SDL_CreateWindow(b'Moonlight SDL3 package test', 0, 0, 64, 64, 8)
        assert window
        try:
            assert sdl.SDL_IsTextInputActive() == 0
            ttf = C.CDLL(str(directory / 'SDL2_ttf.dll'))
            assert ttf.TTF_Init() == 0
            ttf.TTF_Quit()
        finally:
            sdl.SDL_DestroyWindow(window)
            sdl.SDL_Quit()
    result = subprocess.run([str(directory / 'Moonlight.exe'), '--help'], cwd=directory,
                            capture_output=True, timeout=30)
    assert result.returncode == 0
    assert b'Available actions:' in result.stdout
    print('SDL3 3.4.18/sdl2-compat 2.32.74 hashes, x64, SDL_ttf and Moonlight startup passed.')

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--package', type=Path)
    group.add_argument('--runtime-dir', type=Path)
    args = parser.parse_args()
    if args.runtime_dir:
        verify_runtime(args.runtime_dir.resolve())
        return
    with tempfile.TemporaryDirectory(prefix='moonlight-sdl3-package-') as temp:
        destination = Path(temp).resolve()
        with zipfile.ZipFile(args.package) as archive:
            assert archive.testzip() is None
            names = archive.namelist()
            for required in ('Moonlight.exe', 'SDL2.dll', 'SDL3.dll', 'SDL2_ttf.dll',
                             'portable.dat', 'platforms/qwindows.dll'):
                assert required in names, required
            for name in names:
                assert (destination / name).resolve().is_relative_to(destination), name
                assert not name.lower().endswith(('.ini', '.log')), 'Private runtime state in archive'
            archive.extractall(destination)
        subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        '--runtime-dir', str(destination)], check=True)

if __name__ == '__main__':
    main()
