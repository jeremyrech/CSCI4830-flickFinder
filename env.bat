@echo off
cd %~dp0
echo Creating virtual environment...
start /b /wait py -m venv web_environment
echo Done.
call web_environment\Scripts\activate.bat
echo Activated virtual environment.
echo Installing requirements...
start /b py -m pip install -r requirements.txt