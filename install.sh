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
if [ ! -f "pywallet.py" ]; then
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

# Install bsddb3
pip install bsddb3

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Test the installation
echo "Testing installation..."
python3 pywallet.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Build successful!"
    echo ""
    echo "To use the improved pywallet:"
    echo "1. Activate the virtual environment: source pywallet_build_env/bin/activate"
    echo "2. Run pywallet: python3 pywallet.py [options]"
    echo ""
    echo "New features:"
    echo "- Full Python 3 support"
    echo "- --output_keys option for text file output"
    echo "- Support for MB/GB size formats"
else
    echo "Error: Build test failed"
    exit 1
fi