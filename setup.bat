@echo off
setlocal

REM Check if Python is installed and prompt user to install if not present
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python3 is not installed. Please install Python3 manually from https://www.python.org/downloads/
    exit /b 1
)

REM Install virtualenv if not installed
python -m pip show virtualenv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing virtualenv...
    python -m pip install virtualenv
)

REM Create a virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
if exist "requirements.txt" (
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Please provide the requirements file.
    exit /b 1
)

REM Source environment variables from sendgrid.env
if exist "sendgrid.env" (
    echo Sourcing environment variables from sendgrid.env...
    for /f "tokens=1,2 delims==" %%i in (sendgrid.env) do (
        if not "%%i"=="#" set %%i=%%j
    )
) else (
    echo sendgrid.env file not found. Please provide the environment variable file.
    exit /b 1
)

REM Run the Flask application
echo Running the Flask application on port 8888...
python app.py --port 8888

endlocal
