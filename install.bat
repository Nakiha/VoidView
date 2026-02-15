@echo off
REM VoidView 依赖安装脚本 (Windows)

echo Installing VoidView dependencies...

echo.
echo [1/3] Installing shared package...
cd shared
pip install -e .
cd ..

echo.
echo [2/3] Installing server package...
cd server
pip install -e .
cd ..

echo.
echo [3/3] Installing client package...
cd client
pip install -e .
cd ..

echo.
echo ========================================
echo Done! All dependencies installed.
echo ========================================
echo.
echo To start server: python run_server.py
echo To start client: python run_client.py
echo.
pause
