@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set /p VERSION="Entrez le numero de version (ex: 1.0.0) : "
if "%VERSION%"=="" (
    echo [ERREUR] Version requise.
    pause
    exit /b 1
)

python publish_release.py %VERSION%
pause
