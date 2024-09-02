@echo off
echo Creating a virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Activated virtual environment...

pip install -r requirements.txt
ren def_conf.json conf.json
echo Renamed def_conf.json to conf.json 

echo Enter your account settings to the conf.json and run the hamster.bat

pause