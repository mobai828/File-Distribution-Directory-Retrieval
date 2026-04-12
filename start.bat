@echo off
chcp 65001 >nul
title 启动 - 文件分件项目
echo =========================================
echo       正在启动 文件分件 项目...
echo =========================================

:: 检查端口是否被占用
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [警告] 端口 8000 已被占用，项目可能已经在运行！
    echo 请先运行 stop.bat 关闭现有服务，或直接访问 http://127.0.0.1:8000
    echo.
    pause
    exit /b
)

:: 启动后端服务
echo [1/2] 启动后端服务 (端口 8000)...
:: 打开一个新的 cmd 窗口来运行 Python 后端
start "文件分件服务后台" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

:: 等待2秒确保服务有时间启动
timeout /t 2 /nobreak >nul

:: 打开浏览器
echo [2/2] 正在打开浏览器...
start http://127.0.0.1:8000

echo.
echo =========================================
echo 项目启动成功！
echo - 服务运行在: http://127.0.0.1:8000
echo - 若要关闭项目，请双击运行 stop.bat
echo =========================================
timeout /t 3 >nul
