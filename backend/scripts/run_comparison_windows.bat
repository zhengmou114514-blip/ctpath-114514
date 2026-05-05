@echo off
REM 对比实验运行脚本（Windows）
REM 使用ctpath conda环境

echo ========================================
echo 对比实验：TKGR-GPRSCL vs TransE vs RotatE
echo ========================================
echo.

REM 设置Python路径
set PYTHON_EXE=E:\Anaconda3\envs\ctpath\python.exe

REM 检查Python环境
echo 检查Python环境...
%PYTHON_EXE% --version
%PYTHON_EXE% -c "import torch; print('PyTorch:', torch.__version__)"
echo.

REM 运行对比实验
echo 开始运行对比实验...
%PYTHON_EXE% run_comparison.py

echo.
echo ========================================
echo 实验完成！
echo 结果保存在 results/comparison/ 目录
echo ========================================

pause
