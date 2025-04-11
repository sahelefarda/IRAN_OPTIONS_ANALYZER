# IRAN_OPTIONS_ANALYZER
نرم افزار تحلیلی معاملات اختیار معامله برای بازار بورس ایران
# Options Strategy Analyzer - Installation and User Guide

## Overview
Options Strategy Analyzer is a professional tool for analyzing options trading strategies, specifically designed for the Iranian market. This application allows you to create, analyze, and visualize options strategies with a focus on gamma analysis and transaction import capabilities.

## System Requirements
- Windows 10 or later
- Python 3.8 or later
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space

## Installation Instructions

### Step 1: Install Python
If you don't have Python installed:
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, make sure to check "Add Python to PATH"
3. Complete the installation

### Step 2: Install Required Dependencies
1. Open Command Prompt (cmd) as administrator
2. Run the following command to install all required packages:
```
pip install PyQt5 matplotlib numpy scipy pandas openpyxl
```

### Step 3: Extract the Application
1. Extract the contents of `OptionsStrategyAnalyzer.zip` to a folder of your choice
2. Make sure all Python files are in the same directory

## Running the Application
1. Navigate to the folder where you extracted the files
2. Double-click on `run.py` or run it from Command Prompt:
```
python run.py
```

## Using the Application

### Main Interface
The application is divided into three main sections:
1. **Strategy Parameters** - Set underlying price, risk-free rate, days to expiry, and implied volatility
2. **Option Positions** - Add, edit, and manage option positions
3. **Charts** - View profit/loss and Greeks charts for your strategy

### Adding Option Positions
1. Select option type (Call/Put)
2. Select position type (Long/Short)
3. Enter strike price
4. Enter quantity
5. Enter premium
6. Click "Add Position"

### Importing Transactions
1. Click "Import" button or select "File > Import Transactions" from the menu
2. Browse and select your transaction Excel file
3. Review detected transactions and positions
4. Click "Import Positions" to add them to your strategy

### Calculating Strategy Metrics
1. After adding positions, click "Calculate" button
2. The application will generate profit/loss and Greeks charts

### Viewing Charts
The application provides several chart tabs:
- **Profit/Loss** - Shows potential profit and loss across different prices
- **Delta** - Shows how the strategy value changes with underlying price
- **Gamma** - Shows the rate of change of delta
- **Theta** - Shows time decay effect
- **Vega** - Shows sensitivity to volatility changes

### Advanced Charts
Access advanced charts from the "Tools > Advanced Charts" menu:
- **Gamma Surface** - 3D visualization of gamma across strikes and time
- **Gamma/Theta Ratio** - Useful for gamma scalping strategies
- **All Greeks Comparison** - Normalized comparison of all Greeks

### Saving and Loading Strategies
- **Save Strategy**: File > Save Strategy
- **Load Strategy**: File > Load Strategy
- **Export Charts**: File > Export Charts

## Transaction File Format
The application supports importing transaction files in Excel format with the following columns:
- تاریخ (Date)
- شرح (Description)
- بدهکار (Debit)
- بستانکار (Credit)
- مانده (Balance)

The description field should contain option transaction details in the format:
- Buy: خرید [quantity] سهم [symbol] به نرخ [price]
- Sell: فروش [quantity] سهم [symbol] به نرخ [price]

## Troubleshooting

### Common Issues
1. **Application doesn't start**
   - Ensure Python is installed correctly
   - Verify all dependencies are installed
   - Check that all .py files are in the same directory

2. **Charts don't display**
   - Ensure matplotlib is installed correctly
   - Try restarting the application

3. **Transaction import fails**
   - Verify your Excel file has the required columns
   - Check that transaction descriptions follow the expected format

### Getting Help
If you encounter any issues not covered in this guide, please contact support with a description of the problem and any error messages you receive.

## Keyboard Shortcuts
- Ctrl+N: New Strategy
- Ctrl+S: Save Strategy
- Ctrl+O: Load Strategy
- Ctrl+I: Import Transactions
- F5: Calculate Strategy Metrics
- Ctrl+Q: Exit

سلب مسؤلیت:
این پروژه جهت توسعه نرم افزار مدیریت معاملات و موقعیت های اختیار معامله در بازار بورس ایران است و هر گونه استفاده واقعی از خروجی آن با مسولیت خود کاربر می باشد.
