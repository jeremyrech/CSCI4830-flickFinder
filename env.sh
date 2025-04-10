#!/bin/bash
echo Creating virtual environment...
py -m venv web_environment
echo Done.
source web_environment/bin/activate
echo Activated virtual environment.
echo Installing requirements...
py -m pip install -r requirements.txt