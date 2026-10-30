@echo off
title XboxOS Build Wizard
color 0B
setlocal

cls
echo.
echo ==========================================
echo            XboxOS Build Wizard
echo                 Version 0.2
echo ==========================================
echo.
echo This wizard installs dependencies and builds XboxOS.
echo.
pause

:: -------------------------------
:: Python Check
:: -------------------------------
cls
echo [1/5] Checking Python...
where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo Python was not found.
        echo Please install Python first.
        pause
        exit /b 1
    )
    set "PYTHON=python"
) else (
    set "PYTHON=py"
)
%PYTHON% --version

:: -------------------------------
:: Install Requirements
:: -------------------------------
cls
echo [2/5] Installing requirements...
if not exist requirements.txt (
    color 0C
    echo requirements.txt was not found.
    pause
    exit /b 1
)
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo Failed to install requirements.
    pause
    exit /b 1
)

:: -------------------------------
:: Check PyInstaller
:: -------------------------------
cls
echo [3/5] Checking PyInstaller...
%PYTHON% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    %PYTHON% -m pip install pyinstaller
    if errorlevel 1 (
        color 0C
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

:: -------------------------------
:: Clean Old Builds
:: -------------------------------
cls
echo [4/5] Cleaning old builds...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist XboxOS.spec del /Q XboxOS.spec
if exist main.spec del /Q main.spec

:: -------------------------------
:: Build XboxOS
:: -------------------------------
cls
echo [5/5] Building XboxOS...
%PYTHON% -m PyInstaller ^
 --onedir ^
 --windowed ^
 --clean ^
 --name XboxOS ^
 --icon=assets\Xbox.ico ^
 main.py

if errorlevel 1 (
    color 0C
    echo.
    echo Build failed.
    pause
    exit /b 1
)

color 0A
echo.
echo ==========================================
echo          XboxOS Build Complete!
echo ==========================================
echo.
echo Output: dist\XboxOS\XboxOS.exe
echo.
pause
exit /b 0
