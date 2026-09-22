@echo off
setlocal

title Remote VM Agent Build

echo.
echo ==========================================
echo    Remote VM Agent otomatik derleme
echo ==========================================
echo.

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"

set "AGENT_DIR=%ROOT%agent"
set "AGENT_FILE=%AGENT_DIR%\agent.py"
set "CONFIG_FILE=%AGENT_DIR%\config.json"
set "DIST_DIR=%AGENT_DIR%\dist"
set "BUILD_DIR=%AGENT_DIR%\build"
set "SPEC_FILE=%AGENT_DIR%\agent.spec"

set "ISS_FILE=%ROOT%installer\RemoteVMAgentSetup.iss"
set "INSTALLER_FILE=%ROOT%installer\Output\RemoteVMAgentSetup.exe"

set "DOWNLOADS_DIR=%ROOT%backend\downloads"
set "DOWNLOAD_FILE=%DOWNLOADS_DIR%\RemoteVMAgentSetup.exe"

echo [1/6] Dosyalar kontrol ediliyor...

if not exist "%PYTHON%" goto python_error
if not exist "%AGENT_FILE%" goto agent_error
if not exist "%CONFIG_FILE%" goto config_error
if not exist "%ISS_FILE%" goto iss_error

echo Dosyalar bulundu.

echo.
echo [2/6] Eski derleme dosyalari temizleniyor...

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%SPEC_FILE%" del /q "%SPEC_FILE%"

if exist "%INSTALLER_FILE%" del /q "%INSTALLER_FILE%"
if exist "%DOWNLOAD_FILE%" del /q "%DOWNLOAD_FILE%"

echo Temizleme tamamlandi.

echo.
echo [3/6] Agent PyInstaller ile derleniyor...

"%PYTHON%" -m PyInstaller --onefile --clean --name agent --uac-admin --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" --specpath "%AGENT_DIR%" "%AGENT_FILE%"

if errorlevel 1 goto build_error

if not exist "%DIST_DIR%\agent.exe" goto exe_error

echo Agent basariyla derlendi.

echo.
echo [4/6] config.json kopyalaniyor...

copy /y "%CONFIG_FILE%" "%DIST_DIR%\config.json" >nul

if errorlevel 1 goto config_copy_error

echo config.json kopyalandi.

echo.
echo [5/6] Inno Setup installer derleniyor...

set "ISCC="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
)

if not defined ISCC if exist "C:\Program Files\Inno Setup 7\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 7\ISCC.exe"
)

if not defined ISCC goto inno_error

"%ISCC%" "%ISS_FILE%"

if errorlevel 1 goto installer_build_error

if not exist "%INSTALLER_FILE%" goto installer_missing_error

echo Installer basariyla derlendi.

echo.
echo [6/6] Installer Flask downloads klasorune kopyalaniyor...

if not exist "%DOWNLOADS_DIR%" mkdir "%DOWNLOADS_DIR%"

copy /y "%INSTALLER_FILE%" "%DOWNLOAD_FILE%" >nul

if errorlevel 1 goto installer_copy_error

echo.
echo ==========================================
echo    DERLEME BASARIYLA TAMAMLANDI
echo ==========================================
echo.
echo Agent:
echo %DIST_DIR%\agent.exe
echo.
echo Config:
echo %DIST_DIR%\config.json
echo.
echo Installer:
echo %INSTALLER_FILE%
echo.
echo Flask indirme dosyasi:
echo %DOWNLOAD_FILE%
echo.
echo Indirme adresi:
echo http://172.20.194.9:5000/download/agent
echo.
pause
exit /b 0

:python_error
echo HATA: Python bulunamadi:
echo %PYTHON%
goto error

:agent_error
echo HATA: agent.py bulunamadi:
echo %AGENT_FILE%
goto error

:config_error
echo HATA: config.json bulunamadi:
echo %CONFIG_FILE%
goto error

:iss_error
echo HATA: Inno Setup dosyasi bulunamadi:
echo %ISS_FILE%
goto error

:build_error
echo HATA: PyInstaller derlemesi basarisiz oldu.
goto error

:exe_error
echo HATA: agent.exe olusturulamadi.
goto error

:config_copy_error
echo HATA: config.json dist klasorune kopyalanamadi.
goto error

:inno_error
echo HATA: Inno Setup Compiler (ISCC.exe) bulunamadi.
echo Lutfen Inno Setup kurulumunu kontrol edin.
goto error

:installer_build_error
echo HATA: Inno Setup derlemesi basarisiz oldu.
goto error

:installer_missing_error
echo HATA: Installer dosyasi bulunamadi:
echo %INSTALLER_FILE%
goto error

:installer_copy_error
echo HATA: Installer backend downloads klasorune kopyalanamadi.
goto error

:error
echo.
echo ==========================================
echo    DERLEME BASARISIZ OLDU
echo ==========================================
echo.
pause
exit /b 1