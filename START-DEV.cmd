@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 goto no_node
node "scripts\preview-site.mjs" --check-node
if errorlevel 1 goto failed
if exist "node_modules\.package-lock.json" goto run
call npm.cmd ci
if errorlevel 1 goto failed
:run
call npm.cmd run dev -- --host 127.0.0.1
if errorlevel 1 goto failed
exit /b 0
:no_node
echo 请先安装 Node.js LTS 24，然后重新双击本文件。
echo 安装页面：https://nodejs.org/
:failed
echo.
echo 请保留上面的错误信息，并查看包内 QUICKSTART.md。
pause
exit /b 1
