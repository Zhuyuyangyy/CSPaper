@echo off
chcp 65001 >nul
echo ========================================
echo    CSPaper & MedPaper 论文生成系统
echo    全自动启动脚本 v2.0
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 创建必要目录
echo [1/4] 创建必要目录...
if not exist "data\papers" mkdir data\papers
if not exist "data\exports" mkdir data\exports
if not exist "data\charts" mkdir data\charts
echo      完成

:: 安装依赖
echo [2/4] 检查Python依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo      安装后端依赖...
    pip install fastapi uvicorn pydantic python-docx reportlab sse-starlette -q
)
echo      完成

:: 启动后端
echo [3/4] 启动后端服务 (端口 8000)...
start "PaperBackend" cmd /c "cd /d %~dp0 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
echo      等待后端就绪...
timeout /t 5 /nobreak >nul

:: 启动CSPaper前端
echo [4/4] 启动前端服务...
echo.
echo ========================================
echo    服务已启动！
echo ========================================
echo.
echo    后端 API:  http://localhost:8000
echo    CSPaper:  http://localhost:9091
echo    MedPaper: http://localhost:9090
echo.
echo    按任意键打开浏览器...
pause >nul

:: 打开浏览器
start http://localhost:9091
start http://localhost:9090

echo.
echo    系统运行中，关闭此窗口不会停止服务
echo    如需停止，请关闭所有相关窗口
pause
