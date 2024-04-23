@echo off
echo Activating virtual environment...
call "C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\venv\Scripts\activate.bat"

echo Running the Python script...
python compile_and_upload_update.py

echo Deactivating virtual environment...
call "C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\venv\Scripts\deactivate.bat"

echo Done.
pause