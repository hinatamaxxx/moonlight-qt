@echo off
rem Local incremental build of Moonlight (Windows x64, Release).
rem Only changed files are recompiled. Output: build\dev-x64\deploy\Moonlight.exe
rem Use "local-build.bat clean" to rebuild everything from scratch.
setlocal enableDelayedExpansion

set SOURCE_ROOT=%~dp0
set SOURCE_ROOT=%SOURCE_ROOT:~0,-1%
if not defined QT_BIN set QT_BIN=C:\Qt\6.12.0\msvc2022_64\bin
set BUILD_FOLDER=%SOURCE_ROOT%\build\dev-x64\build
set DEPLOY_FOLDER=%SOURCE_ROOT%\build\dev-x64\deploy

if not exist "%QT_BIN%\qmake.exe" (
    echo Qt was not found in %QT_BIN%. Set QT_BIN to your Qt bin folder.
    exit /b 1
)
rem A stray quote in PATH breaks cmd's parsing, so drop any quotes first
set "PATH=!PATH:"=!"
set "PATH=!QT_BIN!;!PATH!"

if /I "%~1"=="clean" (
    echo Removing previous local build
    if exist "%SOURCE_ROOT%\build\dev-x64" rmdir /s /q "%SOURCE_ROOT%\build\dev-x64"
)

rem Find Visual Studio and set up the x64 compiler
call "%SOURCE_ROOT%\scripts\find-vswhere.bat"
if !ERRORLEVEL! NEQ 0 goto Error
for /f "usebackq delims=" %%i in (`%VSWHERE% -latest -products * -property installationPath`) do (
    call "%%i\VC\Auxiliary\Build\vcvarsall.bat" AMD64 >nul
)
if !ERRORLEVEL! NEQ 0 goto Error
for /f "usebackq delims=" %%i in (`%VSWHERE% -latest -products * -find VC\Redist\MSVC\*\x64\Microsoft.VC*.CRT`) do set VC_REDIST_DLL_PATH=%%i

if not exist "%BUILD_FOLDER%" mkdir "%BUILD_FOLDER%"
if not exist "%DEPLOY_FOLDER%" mkdir "%DEPLOY_FOLDER%"

pushd "%BUILD_FOLDER%"
if not exist Makefile (
    echo Configuring the project
    qmake.exe "%SOURCE_ROOT%\moonlight-qt.pro"
    if !ERRORLEVEL! NEQ 0 goto ErrorPop
)

echo Compiling Moonlight
rem /MP lets the compiler build several files in parallel
set CL=/MP
nmake /nologo release
if !ERRORLEVEL! NEQ 0 goto ErrorPop
popd

if not exist "%DEPLOY_FOLDER%\Qt6Core.dll" (
    echo Preparing the deployment folder for the first time
    copy /y "%SOURCE_ROOT%\libs\windows\lib\x64\*.dll" "%DEPLOY_FOLDER%" >nul
    if !ERRORLEVEL! NEQ 0 goto Error
    copy /y "%SOURCE_ROOT%\app\SDL_GameControllerDB\gamecontrollerdb.txt" "%DEPLOY_FOLDER%" >nul
    if !ERRORLEVEL! NEQ 0 goto Error
    copy /y "!VC_REDIST_DLL_PATH!\*.dll" "%DEPLOY_FOLDER%" >nul
    if !ERRORLEVEL! NEQ 0 goto Error
    windeployqt.exe --dir "%DEPLOY_FOLDER%" --release --qmldir "%SOURCE_ROOT%\app\gui" --no-opengl-sw --no-compiler-runtime --no-sql --no-system-d3d-compiler --no-system-dxc-compiler --skip-plugin-types qmltooling,generic --no-ffmpeg --force-openssl "%BUILD_FOLDER%\app\release\Moonlight.exe"
    if !ERRORLEVEL! NEQ 0 goto Error
    rem Keep settings and pairing inside this folder
    echo. > "%DEPLOY_FOLDER%\portable.dat"
)

copy /y "%BUILD_FOLDER%\AntiHooking\release\AntiHooking.dll" "%DEPLOY_FOLDER%" >nul
if !ERRORLEVEL! NEQ 0 goto Error
copy /y "%BUILD_FOLDER%\app\release\Moonlight.exe" "%DEPLOY_FOLDER%" >nul
if !ERRORLEVEL! NEQ 0 goto Error

echo.
echo Build successful: %DEPLOY_FOLDER%\Moonlight.exe
exit /b 0

:ErrorPop
popd
:Error
echo Build failed!
exit /b 1
