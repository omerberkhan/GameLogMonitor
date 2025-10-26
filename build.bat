@echo off
echo Building Game Log Monitor Application...

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install required packages!
    exit /b 1
)

:: Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install PyInstaller!
    exit /b 1
)

:: Build the executable using our spec file
echo Building executable...
pyinstaller --clean GameLogMonitor.spec
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build executable!
    exit /b 1
)

echo.
echo Build completed successfully!
echo The executable is located in the dist folder.
echo.

pause 