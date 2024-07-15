#!/bin/bash

# Function to check and install Python on macOS
install_python_mac() {
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo "Installing Python..."
    brew install python
}

# Function to check and install Python on Windows
install_python_windows() {
    if ! command -v choco &> /dev/null; then
        echo "Chocolatey is not installed. Installing Chocolatey..."
        powershell -NoProfile -ExecutionPolicy Bypass -Command \
        "Set-ExecutionPolicy AllSigned; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
        iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    fi
    echo "Installing Python..."
    choco install python -y
}

# Check if Python is installed and install if not present
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Installing Python3..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_python_mac
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install python3 python3-pip -y
    elif [[ "$OSTYPE" == "msys" ]]; then
        install_python_windows
    else
        echo "Unsupported OS. Please install Python3 manually."
        exit 1
    fi
fi

# Install virtualenv if not installed
if ! pip3 show virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    pip3 install virtualenv
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Please provide the requirements file."
    exit 1
fi

# Source environment variables from sendgrid.env
if [ -f "sendgrid.env" ]; then
    echo "Sourcing environment variables from sendgrid.env..."
    source sendgrid.env
    export $(grep -v '^#' sendgrid.env | xargs)
else
    echo "sendgrid.env file not found. Please provide the environment variable file."
    exit 1
fi

# Run the Flask application with debug mode enabled
echo "Running the Flask application on port 8888 with debug mode..."
FLASK_ENV=development FLASK_APP=app.py flask run --port 8888 --debug
