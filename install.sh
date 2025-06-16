#!/bin/bash

# Build script for Improved Pywallet
# This script sets up the environment and installs dependencies

echo "=== Installing Improved Pywallet ==="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if we're in the right directory
if [ ! -f "pywallet.py" ] && [ ! -f "pywallet/pywallet.py" ]; then
    echo "Error: pywallet.py not found. Please run this script from the project root."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "pywallet_build_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv pywallet_build_env
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source pywallet_build_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required dependencies
echo "Installing bsddb3 (Berkeley DB support)..."
pip install bsddb3
if [ $? -ne 0 ]; then
    echo "Error: Failed to install bsddb3"
    exit 1
fi

echo "Installing cryptographic libraries..."
pip install pycrypto
if [ $? -ne 0 ]; then
    echo "Error: Failed to install pycrypto"
    exit 1
fi

pip install cryptography
if [ $? -ne 0 ]; then
    echo "Error: Failed to install cryptography"
    exit 1
fi

echo "✓ All dependencies installed successfully (bsddb3, pycrypto, cryptography)"

# Test the installation
echo "Testing installation..."

# Determine which pywallet.py to use
if [ -f "pywallet.py" ]; then
    PYWALLET_PATH="pywallet.py"
elif [ -f "pywallet/pywallet.py" ]; then
    PYWALLET_PATH="pywallet/pywallet.py"
fi

python3 "$PYWALLET_PATH" --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Build successful!"
    echo ""
    echo "To use the improved pywallet:"
    echo "1. Use the run_pywallet.sh script: ./run_pywallet.sh [options]"
    echo "   or"
    echo "2. Activate the virtual environment: source pywallet_build_env/bin/activate"
    echo "3. Run pywallet: python3 $PYWALLET_PATH [options]"
    echo ""
    echo "New features:"
    echo "- Full Python 3 support"
    echo "- --output_keys option for text file output"
    echo "- Support for MB/GB size formats"
else
    echo "Error: Build test failed"
    exit 1
fi