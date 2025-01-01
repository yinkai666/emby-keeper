@echo off

where powershell >nul 2>nul
if not %errorlevel% == 0 (
    echo Powershell ������, ����Ҫ��װ Powershell ��ʹ�ø�����.
    (((echo.%cmdcmdline%)|find /I "%~0")>nul) && pause
    exit /b 1
)
if not exist "%~dp0/python-*-embed-*" (
    echo **************************************************
    echo *            ��ȴ�, �������� Embykeeper         *
    echo **************************************************
    powershell Unblock-File -Path '%~dp0downloaders\download_python.ps1'
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_python.ps1" -Version 3.8.10 -TargetDirectory "." || goto :error
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_pip.ps1" -TargetDirectory "python-3.8.10-embed-amd64" || goto :error
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_deps.ps1" -RequirementsFile "%~dp0script\requirements.txt" -PythonPath "%~dp0python-3.8.10-embed-amd64\Scripts\python.exe" || goto :error
    xcopy /y "%~dp0script\Update.bat" "%~dp0"
    echo **************************************************
    echo ��װ���! �������� Embykeeper.
    timeout /t 2 /nobreak > NUL
    cls
)
"%~dp0/python-3.8.10-embed-amd64/python.exe" "script\cli.py" -i
echo.
(((echo.%cmdcmdline%)|find /I "%~0")>nul) && echo | set /p="Embykeeper �ѽ���, �밴������˳�..." & pause>nul

goto :EOF

:error
echo **************************************************
echo ��������, �����˳�, �뷴��������Ϣ.
(((echo.%cmdcmdline%)|find /I "%~0")>nul) && pause
