@echo off
chcp 65001 >nul
echo ==============================================================
echo    CSPaper & MedPaper 论文生成系统 v2.0
echo    全自主智能开发 | 通宵无人值守深度开发模式
echo ==============================================================
echo.
echo [启动信息]
echo   后端API:   http://localhost:8000
echo   API文档:   http://localhost:8000/docs
echo   CSPaper:   http://localhost:9091
echo   MedPaper:  http://localhost:9090
echo.
echo [功能说明]
echo   - 智能大纲生成 ^(^符合学校规范^)
echo   - 全文自动写作
echo   - 参考文献格式化
echo   - 查重率模拟
echo   - 图表自动生成
echo   - DOCX/PDF双格式导出
echo   - 竞赛申报书生成
echo.
echo ==============================================================
echo.

:: 设置工作目录
set WORKSPACE=C:\Users\联想\.openclaw\workspace
cd /d "%WORKSPACE%"

:: 检查Python依赖
echo [1/4] 检查Python依赖...
python -c "import fastapi, uvicorn, pydantic, docx" 2>nul
if %errorlevel% neq 0 (
    echo   安装依赖包...
    pip install fastapi uvicorn pydantic python-docx reportlab sse-starlette -q
)

:: 启动后端服务
echo [2/4] 启动后端服务 ^(端口 8000^)...
start "CSPaper-Backend" cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动CSPaper前端
echo [3/4] 启动CSPaper前端 ^(端口 9091^)...
cd /d "%WORKSPACE%"
for /d %%i in ("DZYY ProjectCSPaper-*") do (
    cd "%%i"
    start "CSPaper-Frontend" cmd /c "npm run dev -- --port 9091 --host"
    cd ..
)

:: 启动MedPaper前端
echo [4/4] 启动MedPaper前端 ^(端口 9090^)...
for /d %%i in ("DZYY ProjectMedPaper-*") do (
    cd "%%i"
    start "MedPaper-Frontend" cmd /c "npm run dev -- --port 9090 --host"
    cd ..
)

:: 打开浏览器
echo.
echo [完成] 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:9091

echo.
echo ==============================================================
echo    系统已全部启动！
echo ==============================================================
echo.
echo    使用说明：
echo    1. CSPaper: http://localhost:9091
echo    2. MedPaper: http://localhost:9090
echo    3. 后端API: http://localhost:8000/docs
echo.
echo    关闭说明：
echo    - 关闭各个命令行窗口即可停止服务
echo    - 或在任务管理器中结束相关进程
echo.
echo    论文生成系统 v2.0 - 全自主智能开发体 OpenClaw
echo ==============================================================
pause
