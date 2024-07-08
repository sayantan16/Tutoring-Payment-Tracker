# Function to check and install Python on Windows
function Install-Python-Windows {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Output "Chocolatey is not installed. Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    }
    Write-Output "Installing Python..."
    choco install python -y
}

# Check if Python is installed and install if not present
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Output "Python3 is not installed. Installing Python3..."
    Install-Python-Windows
}

# Install virtualenv if not installed
if (-not (python -m pip show virtualenv)) {
    Write-Output "Installing virtualenv..."
    python -m pip install virtualenv
}

# Create a virtual environment
if (-not (Test-Path -Path "venv")) {
    Write-Output "Creating virtual environment..."
    python -m venv venv
}

# Activate the virtual environment
Write-Output "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install requirements
if (Test-Path -Path "requirements.txt") {
    Write-Output "Installing requirements..."
    pip install -r requirements.txt
} else {
    Write-Output "requirements.txt not found. Please provide the requirements file."
    exit 1
}

# Source environment variables from sendgrid.env
if (Test-Path -Path "sendgrid.env") {
    Write-Output "Sourcing environment variables from sendgrid.env..."
    Get-Content sendgrid.env | ForEach-Object {
        if ($_ -notmatch "^#") {
            $var = $_.Split("=")
            [System.Environment]::SetEnvironmentVariable($var[0], $var[1])
        }
    }
} else {
    Write-Output "sendgrid.env file not found. Please provide the environment variable file."
    exit 1
}

# Run the Flask application
Write-Output "Running the Flask application on port 8888..."
python app.py --port 8888
