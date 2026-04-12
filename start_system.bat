@echo off
echo ========================================
echo 启动慢性病辅助诊疗系统
echo ========================================
echo.

echo [1/2] 启动后端服务...
start cmd /k "cd /d %~dp0app && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 系统启动完成！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo API文档:  http://localhost:8000/docs
echo.
echo 演示账号:
echo   医生: demo_clinic / demo123456
echo   护士: demo_nurse / demo123456
echo   档案管理员: demo_archivist / demo123456
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:5173
