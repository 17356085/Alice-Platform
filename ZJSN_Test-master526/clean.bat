@echo off
cd /d "%~dp0"
echo 清理测试产物...
rmdir /s /q allure-results 2>nul
rmdir /s /q allure-report 2>nul
rmdir /s /q artifacts 2>nul
rmdir /s /q .pytest_cache 2>nul
del /s /q __pycache__ 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
mkdir allure-results 2>nul
mkdir artifacts\failures 2>nul
echo 清理完成
