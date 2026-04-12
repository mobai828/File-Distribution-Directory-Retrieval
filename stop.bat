@echo off
chcp 65001 >nul
title 关闭 - 文件分件项目
echo =========================================
echo       正在关闭 文件分件 项目...
echo =========================================

echo 正在查找占用 8000 端口的服务...

:: 获取占用 8000 端口并且状态为 LISTENING 的进程 PID
set "PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    set "PID=%%a"
)

if defined PID (
    echo 找到运行在端口 8000 的服务 (进程 ID: %PID%)
    echo 正在终止进程...
    
    :: 强制终止该进程及其子进程
    taskkill /F /T /PID %PID%
    
    if %errorlevel% equ 0 (
        echo [成功] 服务已成功关闭！
    ) else (
        echo [失败] 无法关闭服务，请手动检查是否需要管理员权限。
    )
) else (
    echo [提示] 未检测到运行在端口 8000 的服务，可能已经关闭。
)

echo.
echo =========================================
echo 操作完成。
echo =========================================
pause
