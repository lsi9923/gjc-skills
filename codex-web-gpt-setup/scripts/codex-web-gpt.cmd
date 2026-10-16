@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "TASK_NODE="
where node.exe >nul 2>nul
if not errorlevel 1 set "TASK_NODE=node.exe"
if not defined TASK_NODE if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "TASK_NODE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
if not defined TASK_NODE (
  echo ERROR: Node.js 22 or newer is required. Install Node.js, then run this command again. 1>&2
  exit /b 2
)
"%TASK_NODE%" "%~dp0manage.mjs" %*
exit /b %ERRORLEVEL%
