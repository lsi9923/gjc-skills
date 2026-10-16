@echo off
setlocal EnableExtensions DisableDelayedExpansion
call "%~dp0scripts\codex-web-gpt.cmd" install
exit /b %ERRORLEVEL%
