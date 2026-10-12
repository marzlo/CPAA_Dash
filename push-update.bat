@echo off
REM Double-click this file to commit and push any changes Claude has made
REM in this folder. It's safe to run even if nothing changed.
cd /d "%~dp0"

echo Staging changes...
git add -A

echo Committing...
git commit -m "Update dashboard (%date% %time%)"

echo Catching up with GitHub (the daily workflow commits history.json itself)...
git pull --rebase
if errorlevel 1 (
  echo.
  echo *** The rebase stopped. Tell Claude what this window says before continuing.
  pause
  exit /b 1
)

echo Pushing to GitHub...
git push

echo.
echo Done. You can close this window.
pause
