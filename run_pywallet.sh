#!/bin/bash

# Run script for Improved Pywallet
# This script activates the virtual environment and runs pywallet

# Check if virtual environment exists
if [ ! -d "pywallet_build_env" ]; then
    echo "Error: Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Check if pywallet exists in the root directory
if [ -f "pywallet.py" ]; then
    # Use the pywallet.py in the root directory
    PYWALLET_PATH="pywallet.py"
# Check if pywallet exists in the pywallet directory
elif [ -f "pywallet/pywallet.py" ]; then
    # Use the pywallet.py in the pywallet directory
    PYWALLET_PATH="pywallet/pywallet.py"
else
    echo "Error: pywallet.py not found. Please run this script from the project root."
    exit 1
fi

# Activate virtual environment and run pywallet
source pywallet_build_env/bin/activate

# Check if debug mode is enabled
if [ "$DEBUG_PYWALLET" = "1" ]; then
    # Run with debug wrapper
    python3 debug_pywallet.py "$@"
else
    # Run with error handling
    # Use a temporary file to capture output
    TEMP_OUTPUT=$(mktemp)
    
    # Run pywallet with output redirection
    python3 "$PYWALLET_PATH" "$@" 2>&1 | tee "$TEMP_OUTPUT"
    
    # Check if segmentation fault occurred
    if grep -q "Segmentation fault" "$TEMP_OUTPUT"; then
        echo ""
        echo "====================================================="
        echo "ERROR: Segmentation fault detected during execution."
        echo "This might be due to memory corruption or invalid data."
        echo ""
        echo "Possible solutions:"
        echo "1. Try with a smaller --recov_size value"
        echo "2. Make sure the wallet file is not corrupted"
        echo "3. Try using the --output_keys option to save any keys"
        echo "   that might have been recovered before the crash"
        echo "====================================================="
    fi
    
    # Clean up
    rm -f "$TEMP_OUTPUT"
fi