#!/bin/bash

# Run script for Improved Pywallet
# This script activates the virtual environment and runs pywallet

# Check if virtual environment exists
if [ ! -d "pywallet_build_env" ]; then
    echo "Error: Virtual environment not found. Please run build.sh first."
    exit 1
fi

# Check if pywallet exists
if [ ! -f "pywallet.py" ]; then
    echo "Error: pywallet.py not found. Please run this script from the project root."
    exit 1
fi

# Activate virtual environment and run pywallet
source pywallet_build_env/bin/activate
python3 pywallet.py "$@"