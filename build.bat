@echo off
rem build.bat - ruft build.ps1 auf (funktioniert auch bei
rem eingeschraenkter Execution Policy, ohne Profil).
rem Exitcode: 0 = Build erfolgreich, 1 = Fehler.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
exit /b %ERRORLEVEL%
