# Improved Pywallet - Python 3 Compatible Bitcoin Wallet Tool

This is an improved version of pywallet with full Python 3 support and enhanced recovery features.

## New Features

### 1. **Full Python 3 Support** ✅
- Removed experimental Python 3 warnings
- Fixed all Python 2/3 compatibility issues
- Proper string/bytes handling
- Updated deprecated function calls

### 2. **Enhanced Key Recovery** ✅
- **New `--output_keys` option**: Export recovered keys to a text file instead of creating a wallet
- **Improved size format support**: Now accepts both old (Mo, Gio) and new (MB, GB) formats
- **Better error handling**: Clearer error messages and validation
- **WIF format support**: Recovered keys are now also output in WIF format for easy import into other wallets
- **Berkeley DB BDB2509 Error Fix**: Automatic resolution of database environment conflicts using temporary isolation
- **Fixed UI prompt ordering**: Passphrase instructions now display properly before the input prompt

### 3. **Backward Compatibility** ✅
- All original functionality preserved
- Existing command-line options work unchanged
- Compatible with existing wallet files

## Installation

### Quick Setup
```bash
# Make build script executable and run it
chmod +x install.sh
./install.sh
```

### Manual Setup
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install libdb-dev python3-dev build-essential python3-venv libssl-dev libffi-dev

# Create virtual environment
python3 -m venv pywallet_build_env
source pywallet_build_env/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install bsddb3 pycryptodome cryptography

# Test crypto installation
python3 -c "from Crypto.Cipher import AES; print('✓ Cryptographic libraries working!')"
```

**Note:** The quick setup script (`./install.sh`) now handles all these steps automatically, including system dependency detection for different operating systems (Ubuntu/Debian, CentOS/RHEL, macOS).

## Usage

### Important: Choose the Right Command

**⚠️ IMPORTANT:** There are two different approaches for extracting keys, choose the right one:

#### For Intact Wallet Files (Recommended)
If you have a complete, non-corrupted `wallet.dat` file and know the password:
```bash
# Interactive extraction - shows total keys and lets you choose how many to extract
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=YOUR_PASSWORD --extract_output=keys.txt

# Or specify exact number of keys to extract (non-interactive)
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=YOUR_PASSWORD --extract_output=keys.txt --extract_max_keys=25
```

#### CHOOSE THE RIGHT METHOD:

**🟢 For INTACT wallet files (RECOMMENDED):**
```bash
# Fast, gets ALL keys, works with complete wallet.dat files
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=1234 --extract_output=keys.txt
```

**🔴 For DAMAGED wallet files ONLY:**
```bash
# Slow recovery from corrupted/damaged data - ONLY use if wallet file is broken
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=100MB --output_keys=recovered_keys.txt
```

**❓ Not sure which to use?** Run this first:
```bash
./run_pywallet.sh --count_keys -w your_wallet.dat
# If this works, your wallet is intact → use --extract_advanced
# If this fails, your wallet is damaged → use --recover
```

### Using the Run Script (Recommended)
```bash
# Show help
./run_pywallet.sh --help

# Interactive extraction (RECOMMENDED - analyzes wallet and lets you choose)
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=1234 --extract_output=keys.txt

# Non-interactive extraction with specific number
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=1234 --extract_output=keys.txt --extract_max_keys=50

# Recover keys from damaged data (SLOW - only use for actual recovery)
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=100MB --output_keys=recovered_keys.txt

# Traditional wallet recovery
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=100MB --recov_outputdir=./recovery
```

### Interactive Extraction Workflow
When you run extraction without specifying `--extract_max_keys`, the system will:

1. **Analyze your wallet** - Count total available keys
2. **Show you options** - Display total keys and extraction choices  
3. **Let you choose** - Pick how many keys to extract
4. **Extract precisely** - Get exactly what you requested
5. **Show clear results** - Display extraction summary with percentages

**Example Interactive Session:**
```
STEP 1: Analyzing wallet to count available keys...
==================================================
WALLET KEY COUNT ANALYSIS:
=========================
Total Private Keys Found: 157

STEP 2: Choose number of keys to extract
==================================================
Your wallet contains 157 total private keys.

Options:
  1. Extract all 157 keys
  2. Extract first 10 keys (default)
  3. Extract first 20 keys
  4. Extract first 50 keys
  5. Specify custom number

Enter your choice (1-5): 1
✓ Will extract ALL 157 keys

STEP 3: Extracting keys...
==================================================
Extracting 157 out of 157 total keys

[extraction process...]

✅ EXTRACTION COMPLETED SUCCESSFULLY!
==================================================
📁 Output file: keys.txt
🔑 Keys extracted: 157 out of 157 total
📊 Percentage: 100.0% of wallet
✅ ALL keys from wallet have been extracted!
==================================================
```

### Manual Usage
```bash
# Activate virtual environment
source pywallet_build_env/bin/activate

# Run pywallet
python3 pywallet/pywallet.py [options]
```

## Command Line Options

### Key Extraction Options (For Intact Wallets)

#### `--extract_advanced`
Extract keys from a complete, intact wallet file with known password.
- **Usage**: `--extract_advanced -w wallet.dat --extract_password=PASSWORD`
- **Fast and efficient**: Direct database access, no byte scanning
- **Best for**: Complete wallet files with known passwords

#### `--extract_password=PASSWORD`
Specify the wallet password for key extraction.
- **Usage**: `--extract_password=your_wallet_password`
- **Required with**: `--extract_advanced`
- **Security tip**: Use quotes if password contains special characters

#### `--extract_output=FILENAME`
Specify output file for extracted keys.
- **Usage**: `--extract_output=extracted_keys.txt`
- **Default**: Keys are printed to console if not specified
- **Format**: Same as `--output_keys` (hex and WIF formats)

#### `--extract_max_keys=NUMBER` (Optional)
Limit the number of keys to extract.
- **Usage**: `--extract_max_keys=20`
- **Default**: 10 keys (if not specified)
- **Useful for**: Testing or limiting output size
- **Note**: You can omit this parameter to extract up to 10 keys by default

#### `--count_keys` (Analyze Only)
Count total number of private keys in wallet without extracting them.
- **Usage**: `--count_keys -w wallet.dat`
- **Purpose**: Find out how many total keys are available before extraction
- **Output**: Shows total records, total private keys, and encryption info
- **Provides**: Exact command to extract ALL keys found
- **No password required**: Only counts keys, doesn't decrypt them

### Recovery Options (For Damaged Data)

#### `--output_keys=FILENAME`
Export recovered private keys to a text file instead of creating a wallet.
- **Usage**: `--output_keys=keys.txt`
- **Output format**: Private keys in both hex and WIF formats
- **Includes**: Both compressed and uncompressed versions of each key
- **Use with**: `--recover` option

### Enhanced `--recov_size`
Now supports modern size formats:
- **Old formats**: `20Mo`, `50Gio` (still supported)
- **New formats**: `20MB`, `50GB`, `100MB`, `2GB`
- **Examples**: 
  - `--recov_size=100MB`
  - `--recov_size=2GB`
  - `--recov_size=500MB`
- **Optional for files**: When `--recov_device` points to a file, `--recov_size` becomes optional
  - If not specified, the entire file will be read
  - Example: `--recov_device=/path/to/backup.img` (will read the entire file)

### WIF Format Conversion Tools

#### `--priv2wif=HEXKEY`
Convert a private key in hex format to WIF format.
- **Usage**: `--priv2wif=0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D`
- **Output**: Displays the WIF format of the provided hex private key

#### `--wif2priv=WIFKEY`
Convert a WIF format private key to hex format.
- **Usage**: `--wif2priv=5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ`
- **Output**: Displays the hex format of the provided WIF private key

#### `--wifcheck=WIFKEY`
Check if a WIF format private key is valid.
- **Usage**: `--wifcheck=5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ`
- **Output**: Displays whether the WIF key passes checksum validation

## Key Extraction vs Recovery: What's the Difference?

### `--extract_advanced` (For Intact Wallets)
**Use this when:**
- ✅ You have a complete `wallet.dat` file
- ✅ You know the wallet password
- ✅ The wallet file is not corrupted
- ✅ You want fast key extraction

**How it works:**
- Treats the file as a complete, valid wallet database
- Uses the known password to decrypt keys directly
- Follows normal wallet database structure
- **Fast and efficient**

**Example:**
```bash
./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=1234 --extract_output=keys.txt
```

### `--recover` (For Damaged/Missing Wallet Data)
**Use this when:**
- 🔧 Your wallet file is corrupted or partially deleted
- 🔧 You're scanning a hard drive for wallet remnants
- 🔧 You don't have a complete wallet.dat file
- 🔧 You're working with raw disk images or partitions

**How it works:**
- Scans data byte-by-byte looking for wallet patterns
- Attempts to reconstruct wallet information from fragments
- Requires manual passphrase input during the process
- **Much slower and more intensive**

**Example:**
```bash
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=100MB --output_keys=recovered_keys.txt
```

### Why `--recover` Might Hang
If you use `--recover` on an intact wallet file:
- It will scan the file byte-by-byte (unnecessary and slow)
- It will prompt for passphrases interactively
- It may appear to hang during decryption attempts
- **This is the wrong tool for the job!**

## Examples

### 0. Count Keys Before Extraction (Recommended First Step)
```bash
# Find out how many keys are in your wallet
./run_pywallet.sh --count_keys -w wallets/wallet1.dat
# Output will show: "Total Private Keys Found: 157" 
# and provide exact command to extract all keys
```

### 1. Extract Keys from Intact Wallet (Recommended)
```bash
./run_pywallet.sh --extract_advanced \
    -w wallets/wallet1.dat \
    --extract_password=your_password \
    --extract_output=my_keys.txt \
    --extract_max_keys=100
```

### 2. Basic Key Recovery from Damaged Data
```bash
./run_pywallet.sh --recover \
    --recov_device=/dev/sda1 \
    --recov_size=500MB \
    --output_keys=my_recovered_keys.txt
```

### 2. Large Scale Recovery
```bash
./run_pywallet.sh --recover \
    --recov_device=/dev/sdb1 \
    --recov_size=10GB \
    --output_keys=all_keys.txt
```

### 3. File-based Recovery (with Size Limit)
```bash
./run_pywallet.sh --recover \
    --recov_device=/path/to/disk/image.img \
    --recov_size=1GB \
    --output_keys=recovered.txt
```

### 4. File-based Recovery (Automatic Size Detection)
```bash
./run_pywallet.sh --recover \
    --recov_device=/path/to/backup.img \
    --output_keys=recovered.txt
```

### 5. Traditional Wallet Creation (Unchanged)
```bash
./run_pywallet.sh --recover \
    --recov_device=/dev/sda1 \
    --recov_size=100MB \
    --recov_outputdir=./wallet_recovery
```

### 6. Convert Hex Private Key to WIF
```bash
./run_pywallet.sh --priv2wif=0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D
```

### 7. Convert WIF to Hex Private Key
```bash
./run_pywallet.sh --wif2priv=5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ
```

### 8. Validate a WIF Key
```bash
./run_pywallet.sh --wifcheck=5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ
```

## Output Format

When using `--output_keys`, the text file contains both hex and WIF formats:
```
# Recovered private keys
# Generated by pywallet recovery
# Format: private keys in both hex and WIF formats
# Each key is provided in both uncompressed and compressed format

# HEX FORMAT KEYS:
3c9229289a6125f7fdf1885a77bb12c37a8d3b4962d936f7e3084dece32a3ca1
3c9229289a6125f7fdf1885a77bb12c37a8d3b4962d936f7e3084dece32a3ca101
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85501
...

# WIF FORMAT KEYS:
5JA7QYoYKimso8jHZrUGDLLiqwEJa3uKyUQnpMcPyxP8jNG8acc
KwdMAjGmerYanjeui5SHS7JkmpZvVipYvB2LJGU1ZxJwYvP98617
5Jbm9rrusXMYL8HqtVJWANrKZWGNgMXTYqN9VVvV71TjdphjRPR
KyBwDMRRz5Xd1XVo4JPcgoLiC9UYFNRmYEjXQvBKBBsRZtCNUPWM
...
```

## System Requirements

- **Python**: 3.6 or higher
- **OS**: Linux, macOS, Windows (with WSL)
- **Memory**: Minimum 1GB RAM
- **Storage**: Depends on recovery size

## Troubleshooting

### "Cipher is not defined" Error
If you get an error like: `Error parsing master key: name 'Cipher' is not defined`

**Cause:** The cryptographic libraries (pycryptodome or pycrypto) are not properly installed or not accessible.

**✅ AUTOMATIC FIX:**
The enhanced `install.sh` script now automatically handles this by:
- Installing system dependencies (libssl-dev, libffi-dev, python3-dev)
- Installing both pycryptodome and cryptography libraries
- Testing the installation before completion
- Providing detailed error messages and fixes

**Manual Solutions:**

1. **Quick Fix (Most Common):**
   ```bash
   # Activate the virtual environment
   source pywallet_build_env/bin/activate
   
   # Reinstall pycryptodome
   pip install --force-reinstall pycryptodome
   
   # Test if it works
   python3 -c "from Crypto.Cipher import AES; print('✓ Cipher test passed!')"
   ```

2. **Clean Installation:**
   ```bash
   # Activate virtual environment
   source pywallet_build_env/bin/activate
   
   # Remove conflicting packages
   pip uninstall -y pycrypto pycryptodome
   
   # Install fresh
   pip install pycryptodome
   ```

3. **System Dependencies Fix:**
   ```bash
   # Install required system libraries
   sudo apt-get install libssl-dev libffi-dev python3-dev build-essential
   
   # Then reinstall crypto libraries
   source pywallet_build_env/bin/activate
   pip install --force-reinstall pycryptodome cryptography
   ```

4. **Alternative Installation Method:**
   ```bash
   # If pycryptodome fails, try the older pycrypto
   pip install pycrypto
   ```

5. **Verify Installation:**
   ```bash
   python3 -c "
   try:
       from Crypto.Cipher import AES
       print('✓ Crypto.Cipher available')
   except ImportError:
       try:
           from Cryptodome.Cipher import AES
           print('✓ Cryptodome.Cipher available')
       except ImportError:
           print('✗ Neither Crypto nor Cryptodome available')
   "
   ```

**Why This Error Occurs:**
- Missing system development libraries (libssl-dev, libffi-dev)
- Conflicting pycrypto/pycryptodome installations
- Incomplete pip installation due to compilation errors
- Virtual environment not activated

**If Still Failing:**
1. Delete the virtual environment: `rm -rf pywallet_build_env`
2. Run the installer again: `./install.sh`
3. The enhanced installer will handle all dependencies automatically

### Berkeley DB Error (BDB2509)
If you get an error like: `Error opening wallet: (22, 'Invalid argument -- BDB2509 the log files from a database environment')`

**Cause:** Stale Berkeley DB environment files in the wallet directory.

**✅ FIXED IN VERSION 2.2-py3-improved:**
This issue has been **automatically resolved** in the current version! The `--extract_advanced` command now uses:
- **Temporary directory isolation**: Creates a clean temporary environment for each extraction
- **Progressive database opening**: Tries multiple database access methods automatically
- **Smart fallback system**: Starts with simple direct access, then tries minimal environment, then full environment
- **Automatic cleanup**: Removes all temporary files after extraction

**The fix works automatically - no manual intervention needed!**

**Legacy Manual Solutions** (for older versions or if issues persist):
1. **Remove stale database files:**
   ```bash
   # Navigate to your wallet directory
   cd wallets/
   # Remove Berkeley DB environment files
   rm -f __db.*
   ```

2. **Copy wallet to clean directory:**
   ```bash
   # Create a clean directory
   mkdir clean_wallets
   # Copy only the wallet.dat file (not the __db.* files)
   cp wallets/wallet.dat clean_wallets/
   # Use the clean copy
   ./run_pywallet.sh --extract_advanced -w clean_wallets/wallet.dat --extract_password=PASSWORD --extract_output=keys.txt
   ```

3. **Check wallet file integrity:**
   ```bash
   # Verify the wallet file is not corrupted
   file wallets/wallet.dat
   # Should show: "Berkeley DB (Log, version X, native byte-order)"
   ```

**Technical Details of the Fix:**
The BDB2509 error occurred because the Berkeley DB environment was being opened with the `DB_RECOVER` flag, which created conflicting `__db.*` environment files. The fix implements:

1. **Isolated Temporary Environment**: Each extraction operation uses a fresh temporary directory
2. **Progressive Access Strategy**:
   - First: Direct database access (fastest, no environment files)
   - Second: Minimal environment with memory pool only
   - Third: Full environment without logging
   - Final: Full environment with all flags as fallback
3. **Comprehensive Cleanup**: All temporary files and database environments are properly closed and removed

This ensures that wallet extractions never interfere with each other or leave stale environment files.

### Cipher Not Defined Error
If you get an error like: `Error parsing master key: name 'Cipher' is not defined`

**Error Details:**
This error indicates that the extraction process failed due to a missing cryptographic module. The `Cipher` class, which is part of a cryptographic library, is not available in your Python environment. This class is typically provided by libraries such as `pycrypto`, `PyCryptodome`, or `cryptography`.

**Steps to Resolve:**

1. **Verify Python Environment**: Ensure that you are using the correct Python environment intended for Pywallet. If you set up a virtual environment as suggested in the documentation, make sure it is activated:
   ```bash
   source pywallet_build_env/bin/activate
   ```

2. **Install Required Cryptography Libraries**: Pywallet requires certain cryptography libraries. Install the necessary libraries:
   ```bash
   pip install pycryptodome
   ```
   
   Alternatively, if you suspect other libraries might be needed, you can install the cryptography library:
   ```bash
   pip install cryptography
   ```

3. **Update Dependencies**: Ensure that all Python dependencies are up to date:
   ```bash
   pip install --upgrade pip
   ```

4. **Review Pywallet Setup**: Ensure that you have followed all steps in the installation section of Pywallet's documentation, including installing system dependencies like `libdb-dev`, `python3-dev`, and `build-essential` if necessary:
   ```bash
   sudo apt-get install libdb-dev python3-dev build-essential python3-venv
   ```

5. **Reinstall All Dependencies**: If the issue persists, try reinstalling all dependencies:
   ```bash
   # Activate virtual environment
   source pywallet_build_env/bin/activate
   
   # Reinstall all cryptographic libraries
   pip uninstall pycrypto pycryptodome cryptography -y
   pip install pycryptodome cryptography
   ```

6. **Rerun the Extraction**: After verifying and setting up the necessary environment and dependencies, attempt to run the extraction again:
   ```bash
   ./run_pywallet.sh --extract_advanced -w wallets/wallet1.dat --extract_password=1234 --extract_output=keys.txt
   ```

**Note**: This error typically occurs when the Python environment is incomplete or when cryptographic dependencies were not properly installed during the initial setup. Following the installation steps in order should prevent this issue.

### UI/Prompt Display Issues

**✅ Fixed: Passphrase prompt instructions appearing after input request**
- **Issue**: Previously, the instructions for entering passphrases would appear after the prompt, making it unclear what the user should enter
- **Fix**: Added proper output buffering control to ensure instructions appear before the input prompt
- **Applies to**: `--recover` command when asking for wallet passphrases

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf pywallet_build_env
./install.sh
```

### Permission Issues
```bash
# Make scripts executable
chmod +x install.sh run_pywallet.sh
```

### Missing Dependencies
```bash
# Install system dependencies
sudo apt-get install libdb-dev python3-dev build-essential
```

## Version Information

- **Version**: 2.2-py3-improved
- **Python Support**: 3.6+
- **Based on**: pywallet 2.2
- **Improvements**: Python 3 compatibility, enhanced recovery features

## License

Same as original pywallet project.