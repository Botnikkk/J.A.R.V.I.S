@echo off
echo Starting Instagram Analytics Bot...

:: Check if the virtual environment exists by looking for the activate file
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo First-time setup detected. Creating virtual environment...
    python -m venv venv
    
    echo Activating environment and installing libraries...
    call venv\Scripts\activate
    pip install -r requirements.txt
    
    echo Setup complete!
) ELSE (
    :: If it already exists, just activate it to save time
    call venv\Scripts\activate
)

:: Run the Python script
echo Running bot...
python main.py

:: Keep the terminal open so you can read the results
pause