@echo off
chcp 65001 >nul
cd /d "d:\Desktop\WorkStudy\ZJSN_Test-master526"
setlocal enabledelayedexpansion

echo ============================================ > test_results.txt
echo  全量测试开始 %date% %time% >> test_results.txt
echo ============================================ >> test_results.txt

REM 清理残留进程
taskkill /F /IM chromedriver.exe >nul 2>&1
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 3 /nobreak >nul

REM 清理缓存
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [1/4] equipment + lab >> test_results.txt
python -m pytest script/equipment/ script/lab/ -q --tb=line -o "addopts=" --reruns 0 >> test_results.txt 2>&1
echo. >> test_results.txt
echo [%time%] equipment+lab DONE >> test_results.txt

REM 清理残留
taskkill /F /IM chromedriver.exe >nul 2>&1
timeout /t 5 /nobreak >nul

echo [2/4] personnel >> test_results.txt
python -m pytest script/personnel/ -q --tb=line -o "addopts=" --reruns 0 >> test_results.txt 2>&1
echo. >> test_results.txt
echo [%time%] personnel DONE >> test_results.txt

taskkill /F /IM chromedriver.exe >nul 2>&1
timeout /t 5 /nobreak >nul

echo [3/4] system >> test_results.txt
python -m pytest script/system/ -q --tb=line -o "addopts=" --reruns 0 >> test_results.txt 2>&1
echo. >> test_results.txt
echo [%time%] system DONE >> test_results.txt

taskkill /F /IM chromedriver.exe >nul 2>&1
timeout /t 5 /nobreak >nul

echo [4/4] sales >> test_results.txt
python -m pytest script/sales/ -q --tb=line -o "addopts=" --reruns 0 >> test_results.txt 2>&1
echo. >> test_results.txt
echo [%time%] sales DONE >> test_results.txt

echo ============================================ >> test_results.txt
echo  全量测试结束 %date% %time% >> test_results.txt
echo ============================================ >> test_results.txt
