@echo off
setlocal enableDelayedExpansion
call scripts\find-vswhere.bat
if errorlevel 1 exit /b 1
for /f "usebackq delims=" %%i in (`%VSWHERE% -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
    set "TASK_VS_ROOT=%%i"
    call "%%i\VC\Auxiliary\Build\vcvarsall.bat" AMD64
)
if errorlevel 1 exit /b 1
if not defined TASK_VS_ROOT exit /b 1
set "TASK_CMAKE_GENERATOR=Visual Studio 17 2022"
for /f "usebackq delims=" %%i in (`%VSWHERE% -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion`) do (
    set "TASK_VS_VERSION=%%i"
    if "!TASK_VS_VERSION:~0,2!"=="18" set "TASK_CMAKE_GENERATOR=Visual Studio 18 2026"
)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-sdl3-jis.ps1 %*
exit /b %ERRORLEVEL%
