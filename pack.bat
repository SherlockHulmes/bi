@echo off
echo 正在清理 __pycache__...
for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"

echo 正在打包源码...
powershell -NoProfile -Command "Compress-Archive -Path 'bi_toolkit','core','sql_scripts','scheduler','notifications','data_quality','data_lineage','data_extract','reports','deploy','templates','static','media','manage.py','requirements.txt','run.bat','stop.bat','README.md','.gitignore','.dockerignore' -DestinationPath 'bi-toolkit.zip' -Force"

echo.
if exist bi-toolkit.zip (
    echo 打包成功: bi-toolkit.zip
    dir bi-toolkit.zip
) else (
    echo 打包失败！
)
pause