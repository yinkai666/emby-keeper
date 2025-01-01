@echo off

where powershell >nul 2>nul
if not %errorlevel% == 0 (
    echo Powershell ������, ����Ҫ��װ Powershell ��ʹ�ø�����.
    (((echo.%cmdcmdline%)|find /I "%~0")>nul) && pause
    exit /b 1
)
echo **************************************************
echo *            ��ȴ�, ���ڸ��� Embykeeper         *
echo **************************************************
powershell Unblock-File -Path '%~dp0downloaders\download_python.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_python.ps1" -Version 3.8.10 -TargetDirectory "." || goto :error
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_pip.ps1" -TargetDirectory "python-3.8.10-embed-amd64" || goto :error
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0downloaders\download_deps.ps1" -Update -PythonPath "python-3.8.10-embed-amd64\Scripts\python.exe" || goto :error

echo **************************************************
"%~dp0/python-3.8.10-embed-amd64/python.exe" -c "import embykeeper; print(f'�����ѽ���, ��ǰ�汾Ϊ: {embykeeper.__version__}')"
(((echo.%cmdcmdline%)|find /I "%~0")>nul) && echo | set /p="�밴������˳�..." & pause>nul
goto :EOF

:error
echo **************************************************
echo ��������, �����˳�, �뷴��������Ϣ.
(((echo.%cmdcmdline%)|find /I "%~0")>nul) && pause
