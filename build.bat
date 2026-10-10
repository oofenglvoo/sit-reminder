@echo off
chcp 65001 >nul
echo [1/2] 生成资源文件...
python tools\make_assets.py
if errorlevel 1 goto :error

echo [2/2] 打包 exe...
python -m PyInstaller --clean --noconfirm build.spec
if errorlevel 1 goto :error

echo.
echo 打包完成: dist\SitReminder.exe
goto :eof

:error
echo.
echo 打包失败，请检查上方错误信息。
exit /b 1
