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

# Install system dependencies first
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Detected apt-get (Ubuntu/Debian). Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y libdb-dev python3-dev build-essential python3-venv libssl-dev libffi-dev
    echo "✓ System dependencies installed"
elif command -v yum &> /dev/null; then
    echo "Detected yum (CentOS/RHEL). Installing system dependencies..."
    sudo yum install -y db-devel python3-devel gcc gcc-c++ make python3-venv openssl-devel libffi-devel
    echo "✓ System dependencies installed"
elif command -v brew &> /dev/null; then
    echo "Detected brew (macOS). Installing system dependencies..."
    brew install berkeley-db python@3 openssl libffi
    echo "✓ System dependencies installed"
else
    echo "Warning: Could not detect package manager. Please install these dependencies manually:"
    echo "  - Berkeley DB development libraries (libdb-dev)"
    echo "  - Python 3 development headers (python3-dev)"
    echo "  - Build tools (build-essential, gcc, make)"
    echo "  - SSL development libraries (libssl-dev)"
    echo "  - FFI development libraries (libffi-dev)"
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
fi

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

# Remove any existing conflicting crypto packages first
echo "Cleaning up any existing crypto packages..."
pip uninstall -y pycrypto pycryptodome cryptography 2>/dev/null || true

# Install cryptography first (has fewer dependency conflicts)
echo "Installing cryptography library..."
pip install --upgrade cryptography
if [ $? -ne 0 ]; then
    echo "Error: Failed to install cryptography"
    echo "This is often due to missing system dependencies."
    echo "Please ensure libssl-dev, libffi-dev, and build-essential are installed."
    exit 1
fi
echo "✓ Installed cryptography"

# Install pycryptodome (recommended over pycrypto for better Python 3 support)
echo "Installing pycryptodome (improved cryptographic support)..."
pip install --upgrade pycryptodome
if [ $? -ne 0 ]; then
    echo "Warning: Failed to install pycryptodome, trying alternative installation methods..."
    
    # Try installing with no cache
    echo "Trying installation with --no-cache-dir..."
    pip install --no-cache-dir pycryptodome
    if [ $? -ne 0 ]; then
        echo "Warning: pycryptodome failed, trying fallback pycrypto..."
        pip install pycrypto
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install both pycryptodome and pycrypto"
            echo "Crypto operations may not work properly."
            echo "Please manually install: pip install pycryptodome"
            exit 1
        fi
        echo "✓ Installed pycrypto as fallback"
    else
        echo "✓ Installed pycryptodome (second attempt)"
    fi
else
    echo "✓ Installed pycryptodome"
fi

echo "✓ All dependencies installed successfully (bsddb3, cryptographic libraries)"

# Test the installation
echo "Testing installation..."

# Determine which pywallet.py to use
if [ -f "pywallet.py" ]; then
    PYWALLET_PATH="pywallet.py"
elif [ -f "pywallet/pywallet.py" ]; then
    PYWALLET_PATH="pywallet/pywallet.py"
fi

# Test basic pywallet functionality
python3 "$PYWALLET_PATH" --help > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Build test failed"
    exit 1
fi

# Test cryptographic libraries availability
echo "Testing cryptographic library availability..."
python3 -c "
import sys

# Test Cipher modules
cipher_available = False
cipher_source = ''

try:
    from Crypto.Cipher import AES
    print('✓ Crypto.Cipher (AES) is available')
    cipher_available = True
    cipher_source = 'pycrypto/pycryptodome'
except ImportError as e1:
    try:
        from Cryptodome.Cipher import AES
        print('✓ Cryptodome.Cipher (AES) is available')
        cipher_available = True
        cipher_source = 'pycryptodome'
    except ImportError as e2:
        print('✗ ERROR: Neither Crypto.Cipher nor Cryptodome.Cipher could be imported')
        print('This WILL cause \"Cipher is not defined\" errors during wallet extraction')
        print('Crypto.Cipher error:', str(e1))
        print('Cryptodome.Cipher error:', str(e2))
        cipher_available = False

# Test other required crypto modules
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    print('✓ cryptography.hazmat.primitives.ciphers is available')
except ImportError as e:
    print('✗ WARNING: cryptography.hazmat.primitives.ciphers not available:', str(e))

# Test hashlib
try:
    import hashlib
    print('✓ hashlib is available')
except ImportError as e:
    print('✗ ERROR: hashlib not available:', str(e))

if not cipher_available:
    print()
    print('CRITICAL ERROR: Cipher modules are not available!')
    print('This will cause wallet extraction to fail with \"Cipher is not defined\" errors.')
    print()
    print('TROUBLESHOOTING STEPS:')
    print('1. Try: pip install --force-reinstall pycryptodome')
    print('2. If that fails: pip uninstall pycrypto pycryptodome && pip install pycryptodome')
    print('3. Check system dependencies: sudo apt-get install libssl-dev libffi-dev python3-dev')
    print('4. Try in a fresh virtual environment')
    sys.exit(1)
else:
    print(f'✓ Cipher modules available from: {cipher_source}')
"

if [ $? -eq 0 ]; then
    echo "✓ Cryptographic libraries test passed!"
else
    echo "✗ CRITICAL: Cryptographic library test failed"
    echo "This WILL cause 'Cipher is not defined' errors during wallet operations"
    echo ""
    echo "IMMEDIATE FIXES TO TRY:"
    echo "1. source pywallet_build_env/bin/activate"
    echo "2. pip install --force-reinstall pycryptodome"
    echo "3. If still failing: pip uninstall pycrypto pycryptodome && pip install pycryptodome"
    echo ""
    echo "SYSTEM DEPENDENCY FIXES:"
    echo "sudo apt-get install libssl-dev libffi-dev python3-dev build-essential"
    echo ""
    exit 1
fi

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
echo "- Enhanced cryptographic library support (pycryptodome + cryptography)"
echo "- --output_keys option for text file output"
echo "- Support for MB/GB size formats"
echo "- Automatic system dependency installation"
echo ""
echo "Cryptographic Libraries Installed:"
echo "- pycryptodome/pycrypto: For wallet decryption (AES, etc.)"
echo "- cryptography: For additional crypto operations"
echo "- System libraries: libssl-dev, libffi-dev for crypto compilation"
echo ""
echo "Installation completed successfully!"
echo ""
echo "TROUBLESHOOTING 'Cipher is not defined' errors:"
echo "If you still get this error after installation:"
echo "1. source pywallet_build_env/bin/activate"
echo "2. pip install --force-reinstall pycryptodome"
echo "3. python3 -c \"from Crypto.Cipher import AES; print('Cipher test passed!')\""
echo ""
echo "For more troubleshooting, refer to README.md"