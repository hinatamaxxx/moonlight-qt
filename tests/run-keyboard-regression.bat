@echo off
setlocal
call scripts\find-vswhere.bat
if errorlevel 1 exit /b 1
for /f "usebackq delims=" %%i in (`%VSWHERE% -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
    call "%%i\VC\Auxiliary\Build\vcvarsall.bat" AMD64
)
if errorlevel 1 exit /b 1
python tests\run-keyboard-regression.py
exit /b %ERRORLEVEL%
