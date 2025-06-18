# Smart Pywallet - Universal Bitcoin Wallet Recovery Tool

## 🎯 **One Command for All Wallet Types**

This improved version of pywallet features **smart auto-detection** - you only need to remember **one command** that automatically handles all wallet types and formats.

## ✨ **Key Features**

### 🧠 **Smart Auto-Detection**
- **Automatically detects** wallet format (Berkeley DB, SQLite, damaged files)
- **Chooses optimal method** (fast extraction vs recovery)  
- **Seamless fallback** when one method fails
- **Clear explanations** of what's happening and why

### ⚡ **Unified Command Interface**
- **One command** for all scenarios
- **No more confusion** about which method to use
- **Client-friendly** - works with preferred command syntax
- **Robust handling** of edge cases

### 🔧 **Full Python 3 Support**
- Removed experimental warnings
- Fixed all compatibility issues
- Modern error handling
- Updated dependencies

## 📦 **Installation**

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

# Test installation
python3 -c "from Crypto.Cipher import AES; print('✓ Cryptographic libraries working!')"
```

## 🚀 **Usage - One Universal Command**

### **The Only Command You Need to Remember:**

```bash
./run_pywallet.sh --recover --recov_device=PATH_TO_WALLET --output_keys=output_file.txt
```

**That's it!** The system automatically:
1. 🔍 **Analyzes** your wallet file
2. 🎯 **Detects** the optimal extraction method
3. ⚡ **Attempts** fast extraction first (if wallet is intact)
4. 🔄 **Falls back** to recovery mode (if needed)
5. 📝 **Explains** what it's doing and why

### **Examples**

#### Extract from any wallet file:
```bash
./run_pywallet.sh --recover --recov_device=wallet.dat --output_keys=my_keys.txt
```

#### Extract from wallet in directory:
```bash
./run_pywallet.sh --recover --recov_device=xtest/xtest1/wallet.dat --output_keys=recovered_keys.txt
```

#### Recover from damaged device:
```bash
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=100MB --output_keys=recovered_keys.txt
```

## 🧠 **How Smart Detection Works**

### **Step 1: Analysis**
```
🔍 SMART RECOVERY - Analyzing target...
============================================================
🔍 SMART WALLET DETECTION
============================================================
You used --recover command on: wallet.dat
Auto-analyzing to choose the best extraction method...

Testing if wallet file is intact...
```

### **Step 2: Method Selection**

#### **✅ For Intact Wallets (Fast Path):**
```
✅ Wallet integrity OK - Format: advanced
✅ WALLET IS INTACT - Using Advanced Extraction
============================================================
🎯 RECOMMENDATION: Your wallet file is complete and undamaged.
   Using FAST advanced extraction instead of slow recovery.
   This will get you ALL keys efficiently!

🔑 Enter the wallet password (or press Enter for default '1234'):
Password: [your_password]
⚡ Method: Advanced Extraction (FAST & COMPLETE)
```

#### **🔧 For Damaged Wallets (Recovery Path):**
```
❌ WALLET APPEARS DAMAGED - Using Recovery Method
============================================================
🔧 Your wallet file appears corrupted or damaged.
   Using traditional recovery method to scan for key fragments.
   This will be slower but may recover partial data.
```

#### **🔄 Smart Fallback:**
```
⚠️ Advanced extraction failed: [technical error]
🔄 Automatically falling back to traditional recovery method...
Using password from previous attempt: [password]
Starting recovery.
```

### **Step 3: Results**
```
✅ SUCCESS! 202 unique keys recovered
📂 Keys saved to: recovered_keys.txt
```

## 🎯 **What This Solves**

### **Before (Confusing):**
- ❌ Multiple different commands for different wallet types
- ❌ Users had to guess which command to use
- ❌ Arguments about "correct" vs "wrong" commands
- ❌ Manual fallback when methods failed

### **After (Simple):**
- ✅ **One command** for all wallet types
- ✅ **Automatic detection** and method selection
- ✅ **Smart fallback** when methods fail
- ✅ **Clear explanations** of what's happening
- ✅ **Client satisfaction** - they use their preferred command

## 📊 **Supported Wallet Types**

The smart detection automatically handles:

| Wallet Type | Format | Detection Method | Extraction Method |
|-------------|--------|------------------|-------------------|
| **Bitcoin Core (old)** | Berkeley DB | DB structure analysis | Advanced extraction |
| **Bitcoin Core (new)** | SQLite | File signature detection | Recovery parsing |
| **Damaged/Corrupted** | Any | Error fallback | Recovery scanning |
| **Disk Images** | Raw data | Size/device analysis | Recovery scanning |
| **Backup Files** | Various | Extension + content | Auto-detected method |

## 📁 **Output Format**

All recovered keys are saved in both HEX and WIF formats:

```
# Recovered private keys
# Generated by pywallet recovery
# Format: private keys in both hex and WIF formats

Key #1 (HEX): 3c9229289a6125f7fdf1885a77bb12c37a8d3b4962d936f7e3084dece32a3ca1
Key #1 (WIF): 5JA7QYoYKimso8jHZrUGDLLiqwEJa3uKyUQnpMcPyxP8jNG8acc

Key #2 (HEX): e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Key #2 (WIF): 5Jbm9rrusXMYL8HqtVJWANrKZWGNgMXTYqN9VVvV71TjdphjRPR
...
```

## 🔧 **Command Options**

### **Required Options:**
- `--recover` - Activates smart recovery mode
- `--recov_device=PATH` - Path to wallet file or device
- `--output_keys=FILE` - Output file for recovered keys

### **Optional Options:**
- `--recov_size=SIZE` - Limit recovery size (auto-detected for files)
  - Examples: `100MB`, `2GB`, `500MB`
  - Not needed for wallet files (auto-detected)

### **Size Format Support:**
- **Modern**: `100MB`, `2GB`, `500MB`
- **Legacy**: `100Mo`, `2Gio` (still supported)

## 🏆 **Benefits**

### **For Users:**
- ✅ **Simple**: Only one command to remember
- ✅ **Reliable**: Automatic method selection
- ✅ **Transparent**: Clear explanations of actions
- ✅ **Robust**: Automatic fallback on failures

### **For Support:**
- ✅ **No arguments** about which commands to use
- ✅ **Self-documenting** process with clear output
- ✅ **Handles edge cases** automatically
- ✅ **Client satisfaction** through preference accommodation

## 🚨 **Troubleshooting**

### **"No size specified" Message**
This is normal for wallet files:
```
No size specified. Using full file size: 933888 bytes (0.89 MB)
```
The system automatically detects the file size.

### **"Advanced extraction failed" Message**
This triggers automatic fallback:
```
⚠️ Advanced extraction failed: [error details]
🔄 Automatically falling back to traditional recovery method...
```
This is expected behavior for certain wallet formats.

### **"DB object has been closed" Error**
This is handled automatically by the fallback system. The error is caught and recovery continues with an alternative method.

## 📈 **System Requirements**

- **Python**: 3.6 or higher
- **OS**: Linux, macOS, Windows (with WSL)
- **Memory**: Minimum 1GB RAM (more for large recoveries)
- **Storage**: Space for output files

## 🎉 **Success Stories**

### **Scenario 1: Intact Bitcoin Core Wallet**
```bash
./run_pywallet.sh --recover --recov_device=wallets/wallet1.dat --output_keys=keys.txt
```
**Result**: ✅ Fast extraction, 2001 keys recovered in 30 seconds

### **Scenario 2: SQLite Wallet (newer Bitcoin Core)**
```bash
./run_pywallet.sh --recover --recov_device=xtest/xtest1/wallet.dat --output_keys=keys.txt
```
**Result**: ✅ Auto-fallback to recovery, 202 keys recovered from SQLite format

### **Scenario 3: Damaged Hard Drive**
```bash
./run_pywallet.sh --recover --recov_device=/dev/sda1 --recov_size=500MB --output_keys=keys.txt
```
**Result**: ✅ Deep scan recovery, partial key recovery from damaged sectors

---

## 🎯 **Bottom Line**

**One command. All wallet types. Smart detection. Automatic fallback. Client satisfaction.**

That's the power of smart pywallet - eliminating complexity while maximizing results.

