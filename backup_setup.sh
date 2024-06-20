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
    if ! command -v python3 &> /dev/null; then
        echo "Python3 is not installed. Installing Python3..."
        if ! command -v choco &> /dev/null; then
            echo "Chocolatey is not installed. Installing Chocolatey..."
            if ! command -v pwsh &> /dev/null; then
                echo "PowerShell is not installed. Installing PowerShell..."
                curl -LO https://github.com/PowerShell/PowerShell/releases/download/v7.2.4/PowerShell-7.2.4-win-x64.msi
                msiexec.exe /i PowerShell-7.2.4-win-x64.msi /quiet
                rm PowerShell-7.2.4-win-x64.msi
            fi
            pwsh -NoProfile -ExecutionPolicy Bypass -Command \
            "Set-ExecutionPolicy AllSigned; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
            iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
        fi
        echo "Installing Python..."
        pwsh -NoProfile -ExecutionPolicy Bypass -Command "choco install python -y"
    fi
}

# Check if Python is installed and install if not present
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Python3 is not installed. Installing Python3..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_python_mac
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install python3 python3-pip -y
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
        install_python_windows
    else
        echo "Unsupported OS. Please install Python3 manually."
        exit 1
    fi
fi

# Set Python and Pip commands
PYTHON_CMD=$(command -v python3 || command -v python)
PIP_CMD=$(command -v pip3 || command -v pip)

# Install virtualenv if not installed
if ! $PIP_CMD show virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    $PIP_CMD install virtualenv
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

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
    set -o allexport
    source sendgrid.env
    set +o allexport
else
    echo "sendgrid.env file not found. Please provide the environment variable file."
    exit 1
fi

# Run the Flask application
echo "Running the Flask application on port 8888..."
$PYTHON_CMD app.py --port 8888
