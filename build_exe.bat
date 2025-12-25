@echo off
echo ================================================================================
echo Building Liquidacion OPAEF Executable
echo ================================================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [1/4] Activating virtual environment... OK
echo.

REM Clean previous builds
if exist "build" (
    echo [2/4] Cleaning previous builds...
    rmdir /s /q build
    echo       Cleaned build directory... OK
)
if exist "dist" (
    rmdir /s /q dist
    echo       Cleaned dist directory... OK
)
if exist "*.spec" (
    del /q *.spec
    echo       Cleaned spec files... OK
)
echo.

REM Build executable
echo [3/4] Building executable with PyInstaller...
echo       This may take a few minutes...
echo.

pyinstaller --onefile ^
    --windowed ^
    --name="LiquidacionOPAEF" ^
    --icon=NONE ^
    --add-data "src;src" ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [4/4] Build completed successfully!
    echo.
    echo ================================================================================
    echo Executable created: dist\LiquidacionOPAEF.exe
    echo ================================================================================
    echo.
    echo You can now distribute the file:
    echo   dist\LiquidacionOPAEF.exe
    echo.
    echo This is a portable executable that doesn't require Python installation.
    echo.
) else (
    echo.
    echo [ERROR] Build failed!
    echo Please check the error messages above.
    echo.
)

pause
