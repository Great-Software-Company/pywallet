#!/bin/bash

# Run script for Improved Pywallet with Enhanced Error Diagnostics
# This script activates the virtual environment and runs pywallet with comprehensive error analysis
# 
# Usage Examples:
#   ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat --keys=/path/to/output.txt
#   ./run_pywallet.sh --help
#   DEBUG_PYWALLET=1 ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat
#
# Features:
#   - Pre-execution wallet file validation
#   - Comprehensive error pattern detection
#   - Detailed recovery suggestions
#   - Automatic error log generation for remote debugging
#   - System resource analysis

# Function to display help information
show_help() {
    echo "Pywallet Enhanced Recovery Tool"
    echo "==============================="
    echo ""
    echo "This script provides enhanced error diagnostics and recovery suggestions"
    echo "for Bitcoin wallet recovery operations."
    echo ""
    echo "USAGE:"
    echo "  ./run_pywallet.sh [OPTIONS]"
    echo ""
    echo "COMMON RECOVERY COMMANDS:"
    echo "  # Basic wallet recovery"
    echo "  ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat --keys=/path/to/output.txt"
    echo ""
    echo "  # Recovery with size limit (recommended for large files)"
    echo "  ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat --recov_size=100MB --keys=/path/to/output.txt"
    echo ""
    echo "  # Debug mode (detailed error analysis)"
    echo "  DEBUG_PYWALLET=1 ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat --keys=/path/to/output.txt"
    echo ""
    echo "  # Force recovery mode"
    echo "  ./run_pywallet.sh --recover --recov_device=/path/to/wallet.dat --force --keys=/path/to/output.txt"
    echo ""
    echo "ENHANCED FEATURES:"
    echo "  ✓ Pre-execution wallet file validation"
    echo "  ✓ Automatic error pattern detection"
    echo "  ✓ Specific recovery suggestions based on error type"
    echo "  ✓ System resource analysis"
    echo "  ✓ Comprehensive error logging for remote debugging"
    echo "  ✓ Memory optimization recommendations"
    echo ""
    echo "ERROR HANDLING:"
    echo "  - Segmentation faults: Provides memory optimization suggestions"
    echo "  - Database corruption: Offers alternative recovery methods"
    echo "  - Passphrase issues: Guides through decryption strategies"
    echo "  - File size problems: Recommends chunk processing"
    echo ""
    echo "For more pywallet options, run: python3 pywallet.py --help"
    echo ""
}

# Check for help argument
if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "help" ]; then
    show_help
    exit 0
fi

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

# Function to analyze wallet errors and provide detailed diagnostics
analyze_wallet_errors() {
    local output_file="$1"
    local command_args="$2"
    local exit_code="$3"
    
    # Check for various error patterns and provide specific guidance
    local has_error=false
    
    echo ""
    echo "============================================================"
    echo "WALLET RECOVERY DIAGNOSTIC REPORT"
    echo "============================================================"
    echo "Command executed: $0 $command_args"
    echo "Exit code: $exit_code"
    echo "Timestamp: $(date)"
    echo ""
    
    # Check for segmentation fault
    if grep -q "Segmentation fault\|has stopped unexpectedly" "$output_file"; then
        has_error=true
        echo "🚨 CRITICAL ERROR: Application Crash Detected"
        echo "------------------------------------------------------------"
        echo "The application crashed with a segmentation fault."
        echo "This typically indicates memory corruption or invalid data access."
        echo ""
        echo "IMMEDIATE ACTIONS:"
        echo "1. The wallet file may contain corrupted or invalid data structures"
        echo "2. Try reducing memory usage with smaller recovery chunks"
        echo "3. Attempt alternative recovery methods"
        echo ""
    fi
    
    # Check for database corruption error
    if grep -q "Couldn't open wallet.dat/main\|Database may be corrupted" "$output_file"; then
        has_error=true
        echo "🔧 DATABASE ERROR: Wallet File Access Failed"
        echo "------------------------------------------------------------"
        echo "The wallet database structure appears to be corrupted or unreadable."
        echo ""
        echo "RECOVERY STRATEGIES:"
        echo "1. File Format Issues:"
        echo "   - Verify the file is actually a Bitcoin wallet (.dat file)"
        echo "   - Check file size (should be > 0 bytes and < 2GB typically)"
        echo "   - Ensure file permissions allow reading"
        echo ""
        echo "2. Try Alternative Recovery Methods:"
        if echo "$command_args" | grep -q "\--recover"; then
            echo "   - Current: Using --recover mode (raw recovery)"
            echo "   - Try: Direct key extraction with --dumpwallet"
            echo "   - Try: Hex dump analysis with --hexdump"
        else
            echo "   - Try: Raw recovery mode with --recover"
            echo "   - Try: Force recovery with --recover --force"
        fi
        echo ""
    fi
    
    # Check for passphrase-related issues
    if grep -q "Enter the possible passphrases\|Possible passphrase:" "$output_file"; then
        has_error=true
        echo "🔐 PASSPHRASE PROMPT: Wallet Requires Decryption"
        echo "------------------------------------------------------------"
        echo "The wallet is encrypted and requires passphrase(s) for recovery."
        echo ""
        echo "PASSPHRASE RECOVERY TIPS:"
        echo "1. Common passphrase variations to try:"
        echo "   - Original passphrase with different cases"
        echo "   - Passphrase with numbers added (123, 2023, etc.)"
        echo "   - Passphrase with special characters (!@#$)"
        echo "   - Shortened versions of longer phrases"
        echo ""
        echo "2. If you don't remember the passphrase:"
        echo "   - Try leaving empty (press Enter twice) for unencrypted recovery"
        echo "   - Use dictionary attack tools separately"
        echo "   - Try common passwords you've used before"
        echo ""
    fi
    
    # Check for file size/memory issues
    if grep -q "No size specified\|Using full file size" "$output_file"; then
        local file_size=$(grep "Using full file size" "$output_file" | grep -o '[0-9.]* [MG]B')
        if [ ! -z "$file_size" ]; then
            echo "📊 FILE SIZE ANALYSIS: $file_size"
            echo "------------------------------------------------------------"
            echo "Processing large wallet file. This may cause memory issues."
            echo ""
            echo "OPTIMIZATION SUGGESTIONS:"
            echo "1. For files > 100MB, use --recov_size to limit processing:"
            echo "   --recov_size=50MB    (process first 50MB)"
            echo "   --recov_size=100MB   (process first 100MB)"
            echo ""
            echo "2. For very large files (>500MB):"
            echo "   --recov_size=10MB    (start with small chunks)"
            echo "   --recov_size=1GB     (if you have sufficient RAM)"
            echo ""
        fi
    fi
    
    # Check for successful key extraction
    if grep -q "Potential private keys found\|Private key found" "$output_file"; then
        echo "✅ SUCCESS: Private Keys Detected"
        echo "------------------------------------------------------------"
        local key_count=$(grep -o "Potential private keys found: [0-9]*" "$output_file" | grep -o "[0-9]*")
        if [ ! -z "$key_count" ]; then
            echo "Found $key_count potential private keys in the wallet."
        fi
        echo ""
        echo "NEXT STEPS:"
        echo "1. Verify the extracted keys in a test environment"
        echo "2. Import keys into a secure wallet application"
        echo "3. Check balances before using with real funds"
        echo "4. Keep backup copies of the key file"
        echo ""
        has_error=false
    fi
    
    # Provide recovery command suggestions based on current command
    if [ "$has_error" = true ]; then
        echo "🔄 SUGGESTED RECOVERY COMMANDS:"
        echo "------------------------------------------------------------"
        
        # Extract the wallet file path from command args
        local wallet_file=$(echo "$command_args" | grep -o '\--recov_device=[^ ]*' | cut -d'=' -f2)
        local output_file_arg=$(echo "$command_args" | grep -o '\--[a-z_]*=/[^ ]*\.txt' | head -1)
        
        if [ -z "$wallet_file" ]; then
            wallet_file="<your_wallet_file>"
        fi
        if [ -z "$output_file_arg" ]; then
            output_file_arg="--keys=/home/test/recovered_keys.txt"
        fi
        
        echo "Try these commands in order:"
        echo ""
        echo "1. Small chunk recovery (safest):"
        echo "   ./run_pywallet.sh --recover --recov_device=$wallet_file --recov_size=10MB $output_file_arg"
        echo ""
        echo "2. Force recovery mode:"
        echo "   ./run_pywallet.sh --recover --recov_device=$wallet_file --force $output_file_arg"
        echo ""
        echo "3. Alternative extraction method:"
        echo "   ./run_pywallet.sh --dumpwallet --file=$wallet_file $output_file_arg"
        echo ""
        echo "4. Hex dump analysis (for severely corrupted files):"
        echo "   ./run_pywallet.sh --hexdump --file=$wallet_file > wallet_hexdump.txt"
        echo ""
        echo "5. Debug mode (for detailed error analysis):"
        echo "   DEBUG_PYWALLET=1 ./run_pywallet.sh --recover --recov_device=$wallet_file $output_file_arg"
        echo ""
    fi
    
    # System information for debugging
    echo "🖥️  SYSTEM INFORMATION:"
    echo "------------------------------------------------------------"
    echo "Python version: $(python3 --version 2>&1)"
    echo "Available memory: $(free -h | grep '^Mem:' | awk '{print $7}' 2>/dev/null || echo 'Unknown')"
    echo "Disk space: $(df -h . | tail -1 | awk '{print $4}' 2>/dev/null || echo 'Unknown')"
    echo ""
    
    if [ "$has_error" = true ]; then
        echo "⚠️  If problems persist:"
        echo "------------------------------------------------------------"
        echo "1. Check if the wallet file is actually a Bitcoin Core wallet"
        echo "2. Try with a different wallet recovery tool"
        echo "3. Consider professional data recovery services"
        echo "4. Verify the file hasn't been corrupted during transfer"
        echo ""
    fi
    
    echo "============================================================"
    echo ""
    
    # Create detailed error log for remote debugging
    create_error_log "$output_file" "$command_args" "$exit_code" "$has_error"
}

# Function to create a comprehensive error log for remote debugging
create_error_log() {
    local output_file="$1"
    local command_args="$2"
    local exit_code="$3"
    local has_error="$4"
    
    local error_log="pywallet_report_$(date +%Y%m%d_%H%M%S).log"
    
    echo "📝 Creating detailed diagnostic report: $error_log"
    
    {
        echo "PYWALLET ERROR REPORT"
        echo "===================="
        echo "Timestamp: $(date)"
        echo "Command: $0 $command_args"
        echo "Exit Code: $exit_code"
        echo "Has Error: $has_error"
        echo ""
        
        echo "SYSTEM INFORMATION:"
        echo "-------------------"
        echo "OS: $(uname -a)"
        echo "Python: $(python3 --version 2>&1)"
        echo "Memory: $(free -h 2>/dev/null || echo 'Unknown')"
        echo "Disk Space: $(df -h . 2>/dev/null || echo 'Unknown')"
        echo ""
        
        echo "WALLET FILE ANALYSIS:"
        echo "--------------------"
        local wallet_file=$(echo "$command_args" | grep -o '\--recov_device=[^ ]*' | cut -d'=' -f2)
        if [ ! -z "$wallet_file" ] && [ -f "$wallet_file" ]; then
            echo "File: $wallet_file"
            echo "Size: $(stat -c%s "$wallet_file" 2>/dev/null || echo 'Unknown') bytes"
            echo "Type: $(file "$wallet_file" 2>/dev/null || echo 'Unknown')"
            echo "Permissions: $(ls -la "$wallet_file" 2>/dev/null || echo 'Unknown')"
            echo "MD5: $(md5sum "$wallet_file" 2>/dev/null | cut -d' ' -f1 || echo 'Unknown')"
        else
            echo "No wallet file specified or file not found"
        fi
        echo ""
        
        echo "PROGRAM OUTPUT:"
        echo "---------------"
        if [ -f "$output_file" ]; then
            cat "$output_file"
        else
            echo "No output captured"
        fi
        echo ""
        
        echo "ERROR PATTERNS DETECTED:"
        echo "------------------------"
        if [ -f "$output_file" ]; then
            echo "Segmentation Fault: $(grep -c "Segmentation fault\|has stopped unexpectedly" "$output_file" 2>/dev/null || echo '0')"
            echo "Database Errors: $(grep -c "Couldn't open wallet.dat\|Database may be corrupted" "$output_file" 2>/dev/null || echo '0')"
            echo "Passphrase Prompts: $(grep -c "Enter the possible passphrases\|Possible passphrase:" "$output_file" 2>/dev/null || echo '0')"
            echo "Keys Found: $(grep -c "Potential private keys found\|Private key found" "$output_file" 2>/dev/null || echo '0')"
        fi
        echo ""
        
        echo "ENVIRONMENT:"
        echo "------------"
        echo "Virtual Environment: $(which python3)"
        echo "Pywallet Path: $PYWALLET_PATH"
        echo "Working Directory: $(pwd)"
        echo "User: $(whoami)"
        echo ""
        
    } > "$error_log"
    
    echo "   Diagnostic report saved to: $error_log"
    echo "   You can share this file for remote debugging assistance."
    echo ""
}

# Function to validate wallet file before processing
validate_wallet_file() {
    local command_args="$*"
    
    # Extract wallet file path from various argument formats
    local wallet_file=""
    if echo "$command_args" | grep -q "\--recov_device="; then
        wallet_file=$(echo "$command_args" | grep -o '\--recov_device=[^ ]*' | cut -d'=' -f2)
    elif echo "$command_args" | grep -q "\--file="; then
        wallet_file=$(echo "$command_args" | grep -o '\--file=[^ ]*' | cut -d'=' -f2)
    fi
    
    if [ ! -z "$wallet_file" ] && [ -f "$wallet_file" ]; then
        echo "🔍 PRE-EXECUTION WALLET ANALYSIS"
        echo "============================================================"
        echo "Wallet file: $wallet_file"
        
        # Check file size
        local file_size=$(stat -c%s "$wallet_file" 2>/dev/null || echo "0")
        local file_size_mb=$((file_size / 1024 / 1024))
        echo "File size: $file_size bytes (${file_size_mb}MB)"
        
        # Check file permissions
        if [ ! -r "$wallet_file" ]; then
            echo "⚠️  WARNING: File is not readable. Check permissions."
            echo "   Try: chmod 644 '$wallet_file'"
            echo ""
        fi
        
        # Check if file is empty
        if [ "$file_size" -eq 0 ]; then
            echo "❌ ERROR: Wallet file is empty (0 bytes)"
            echo "   This file cannot contain any wallet data."
            echo "   Please check if you have the correct file."
            echo ""
            return 1
        fi
        
        # Check if file is suspiciously small
        if [ "$file_size" -lt 1024 ]; then
            echo "⚠️  WARNING: File is very small ($file_size bytes)"
            echo "   Bitcoin wallet files are typically at least 1KB"
            echo "   This might not be a valid wallet file."
            echo ""
        fi
        
        # Check if file is very large
        if [ "$file_size_mb" -gt 1000 ]; then
            echo "⚠️  WARNING: File is very large (${file_size_mb}MB)"
            echo "   Large files may cause memory issues or crashes."
            echo "   Consider using --recov_size to limit processing."
            echo "   Suggested: --recov_size=100MB"
            echo ""
        fi
        
        # Try to detect file type
        local file_type=$(file "$wallet_file" 2>/dev/null || echo "unknown")
        echo "File type: $file_type"
        
        # Check for common wallet file patterns
        if echo "$file_type" | grep -q "Berkeley DB"; then
            echo "✅ Good: Detected Berkeley DB format (typical for Bitcoin Core wallets)"
        elif echo "$file_type" | grep -q "data"; then
            echo "ℹ️  Info: Binary data file (could be wallet or corrupted)"
        else
            echo "⚠️  Warning: Unusual file type for a Bitcoin wallet"
        fi
        
        echo "============================================================"
        echo ""
    fi
    
    return 0
}

# Activate virtual environment and run pywallet
source pywallet_build_env/bin/activate

# Validate wallet file before processing
validate_wallet_file "$@"
if [ $? -ne 0 ]; then
    echo "Pre-execution validation failed. Aborting."
    exit 1
fi

# Check if debug mode is enabled
if [ "$DEBUG_PYWALLET" = "1" ]; then
    # Run with debug wrapper
    python3 debug_pywallet.py "$@"
else
    # Run with enhanced error handling
    # Use temporary files to capture output and errors
    TEMP_OUTPUT=$(mktemp)
    TEMP_ERROR=$(mktemp)
    EXIT_CODE=0
    
    # Extract command line arguments for analysis
    COMMAND_ARGS="$*"
    
    # Run pywallet with output redirection
    python3 "$PYWALLET_PATH" "$@" 2>&1 | tee "$TEMP_OUTPUT"
    EXIT_CODE=${PIPESTATUS[0]}
    
    # Analyze the output for specific error patterns
    analyze_wallet_errors "$TEMP_OUTPUT" "$COMMAND_ARGS" "$EXIT_CODE"
    
    # Clean up
    rm -f "$TEMP_OUTPUT" "$TEMP_ERROR"
fi