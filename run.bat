@echo off
chcp 65001 >nul 2>&1
title BI工具箱 - 按 Ctrl+C 停止
color 0A
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║           BI 工具箱 - 一键启动                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM ========================================
REM  [1/6] 检测 Python
REM ========================================
echo  [1/6] 检测 Python 环境...
set PYTHON_CMD=

where python >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set PYTHON_CMD=%%i
    goto :python_found
)

where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    goto :python_found
)

if exist "D:\anaconda\python.exe" (
    set PYTHON_CMD=D:\anaconda\python.exe
    goto :python_found
)

if exist "C:\Python39\python.exe" (
    set PYTHON_CMD=C:\Python39\python.exe
    goto :python_found
)

if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    goto :python_found
)

if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :python_found
)

if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto :python_found
)

echo  [错误] 未找到 Python！
echo  请先安装 Python 3.7+ 下载地址：
echo  https://www.python.org/downloads/
echo.
pause
exit /b 1

:python_found
for /f "delims=" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set PY_VER=%%v
echo  [√] 已找到 %PY_VER%: %PYTHON_CMD%
echo.

REM ========================================
REM  [2/6] 安装依赖
REM ========================================
echo  [2/6] 检查并安装依赖...

%PYTHON_CMD% -c "import django" >nul 2>&1
if %errorlevel%==0 (
    echo  [√] Django 已安装，跳过依赖安装
) else (
    echo  [i] 首次运行，正在安装依赖（可能需要几分钟）...
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet
    if %errorlevel%==0 (
        echo  [√] 依赖安装完成
    ) else (
        echo  [!] 依赖安装失败，请检查网络连接
        echo  可手动执行: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo.

REM ========================================
REM  [3/6] 数据库迁移
REM ========================================
echo  [3/6] 执行数据库迁移...
%PYTHON_CMD% manage.py migrate --noinput >nul 2>&1
if %errorlevel%==0 (
    echo  [√] 数据库迁移完成
) else (
    echo  [!] 数据库迁移失败，尝试详细输出...
    %PYTHON_CMD% manage.py migrate --noinput
)
echo.

REM ========================================
REM  [4/6] 创建管理员账户
REM ========================================
echo  [4/6] 检查管理员账户...
%PYTHON_CMD% manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('EXISTS' if User.objects.filter(username='admin').exists() else 'NOT_EXISTS')" 2>nul | find "NOT_EXISTS" >nul
if %errorlevel%==0 (
    %PYTHON_CMD% manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', '', 'admin123'); print('CREATED')" 2>nul
    echo  [√] 管理员账户已创建
    echo      用户名: admin
    echo      密码:   admin123
    echo      (请登录后修改密码！)
) else (
    echo  [√] 管理员账户已存在
)
echo.

REM ========================================
REM  [5/6] 启动后台服务（Redis/Celery）
REM ========================================
echo  [5/6] 启动后台服务...

REM 检测 Redis
set REDIS_OK=0
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I "redis-server.exe" >NUL
if %errorlevel%==0 (
    echo  [√] Redis 已在运行
    set REDIS_OK=1
) else (
    if exist "C:\Redis\redis-server.exe" (
        echo  [i] 正在启动 Redis...
        start "Redis" /MIN C:\Redis\redis-server.exe
        timeout /t 2 >nul
        set REDIS_OK=1
        echo  [√] Redis 启动完成
    ) else (
        echo  [!] 未检测到 Redis，定时任务功能将不可用
        echo      如需定时任务，请安装 Redis
    )
)

if %REDIS_OK%==1 (
    REM 启动 Celery Worker
    echo  [i] 正在启动 Celery Worker...
    start "Celery Worker" /MIN /D "%~dp0" %PYTHON_CMD% -m celery -A bi_toolkit worker -l info -f celery_worker.log --pool=threads --concurrency=4

    REM 清理旧的 Celery Beat 调度文件
    del /Q "%~dp0celerybeat-schedule*" 2>nul

    REM 启动 Celery Beat
    echo  [i] 正在启动 Celery Beat...
    start "Celery Beat" /MIN /D "%~dp0" %PYTHON_CMD% -m celery -A bi_toolkit beat -l info -f celery_beat.log

    timeout /t 3 >nul
    echo  [√] Celery 服务已启动
) else (
    echo  [i] 跳过 Celery 服务
)
echo.

REM ========================================
REM  [6/6] 启动 Django 并打开浏览器
REM ========================================
echo  [6/6] 启动 BI 工具箱...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  BI 工具箱已启动！                               ║
echo  ║                                                  ║
echo  ║  访问地址: http://127.0.0.1:8000                 ║
echo  ║  管理后台: http://127.0.0.1:8000/admin/          ║
echo  ║  账号: admin   密码: admin123                    ║
echo  ║                                                  ║
echo  ║  按 Ctrl+C 停止服务                              ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM 延迟 3 秒后自动打开浏览器
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8000"

REM 启动 Django（前台运行）
%PYTHON_CMD% manage.py runserver 0.0.0.0:8000
pause