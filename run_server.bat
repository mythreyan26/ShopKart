@echo off
title ShopKart Dev Server
cd /d "%~dp0"
echo ========================================================
echo          Starting ShopKart Development Server...
echo ========================================================
echo Storefront URL:    http://127.0.0.1:8000/
echo Admin Console URL: http://127.0.0.1:8000/admin/
echo Admin Login URL:   http://127.0.0.1:8000/admin/login/
echo.
echo Press Ctrl+C in this window anytime to stop the server.
echo ========================================================
python manage.py runserver 0.0.0.0:8000
pause
