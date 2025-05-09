#!/bin/bash
echo Creating virtual environment...
wait
python3 -m venv web_environment
wait
echo Done.
source web_environment/bin/activate
wait
echo Activated virtual environment.
echo Installing requirements...
python3 -m pip install -r requirements.txt