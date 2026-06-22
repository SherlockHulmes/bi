@echo off
chcp 65001 >nul 2>&1
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║           BI 工具箱 - 正在停止...                ║
echo  ╚══════════════════════════════════════════════════╝
echo.

echo  [1/3] 停止 Django...
taskkill /FI "WINDOWTITLE eq BI工具箱 - 按 Ctrl+C 停止" /F 2>nul
echo  [√] Django 已停止

echo  [2/3] 停止 Celery Beat...
taskkill /FI "WINDOWTITLE eq Celery Beat" /F 2>nul
echo  [√] Celery Beat 已停止

echo  [3/3] 停止 Celery Worker...
taskkill /FI "WINDOWTITLE eq Celery Worker" /F 2>nul
echo  [√] Celery Worker 已停止

echo.
echo  所有服务已停止。
echo.
pause