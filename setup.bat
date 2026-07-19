@echo off
title XboxOS Build Wizard
color 0B
setlocal EnableDelayedExpansion

cls
echo.
echo ==========================================
echo            XboxOS Build Wizard
echo                 Version 0.1
echo ==========================================
echo.
echo Welcome!
echo.
echo This wizard will build XboxOS into
echo a standalone Windows executable.
echo.
pause


:: -------------------------------
:: Python Check
:: -------------------------------

cls
echo.
echo [1/5] Checking Python...
echo.

where py >nul 2>&1

if %errorlevel%==0 (
    set PYTHON=py
) else (
    where python >nul 2>&1

    if %errorlevel%==0 (
        set PYTHON=python
    ) else (
        color 0C
        echo Python was not found.
        echo.
        echo Please install Python first.
        echo https://www.python.org/downloads/
        pause
        exit /b
    )
)

echo Python detected!
echo.
pause


:: -------------------------------
:: Check PyInstaller
:: -------------------------------

cls
echo.
echo [2/5] Checking PyInstaller...
echo.

%PYTHON% -m PyInstaller --version >nul 2>&1

if errorlevel 1 (
    echo PyInstaller not found.
    echo.
    echo Installing PyInstaller...
    echo.

    %PYTHON% -m pip install pyinstaller

    if errorlevel 1 (
        color 0C
        echo.
        echo Failed to install PyInstaller.
        pause
        exit /b
    )
)

echo PyInstaller is ready.
echo.
pause


:: -------------------------------
:: Clean Old Builds
:: -------------------------------

cls
echo.
echo [3/5] Cleaning old builds...
echo.

if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist XboxOS.spec del /Q XboxOS.spec
if exist main.spec del /Q main.spec

echo Done.
echo.
pause


:: -------------------------------
:: Build XboxOS
:: -------------------------------

cls
echo.
echo [4/5] Building XboxOS...
echo.

%PYTHON% -m PyInstaller ^
--onedir ^
--windowed ^
--clean ^
--name XboxOS ^
--icon=assets\xboxos.ico ^
main.py

if errorlevel 1 (
    color 0C
    echo.
    echo Build failed.
    pause
    exit /b
)

echo.
echo Build successful!
echo.
pause


:: -------------------------------
:: Finish
:: -------------------------------

cls
color 0A

echo.
echo ==========================================
echo          XboxOS Build Complete!
echo ==========================================
echo.
echo Your executable has been created.
echo.
echo Location:
echo.
echo     dist\XboxOS\
echo.
echo Main executable:
echo.
echo     XboxOS.exe
echo.
echo You can now share the entire
echo "dist\XboxOS" folder.
echo.
echo Enjoy XboxOS!
echo.

pause
exit