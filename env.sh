#!/bin/bash
echo Creating virtual environment...
python3 -m venv web_environment
echo Done.
source web_environment/bin/activate
echo Activated virtual environment.
echo Installing requirements...
python3 -m pip install -r requirements.txt