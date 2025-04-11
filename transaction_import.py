import pandas as pd
import re
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
                            QMessageBox, QGroupBox, QFormLayout, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt

class TransactionAnalyzer:
    """Class for analyzing transaction files and extracting option positions"""
    
    @staticmethod
    def parse_transaction_file(file_path):
        """Parse transaction file and extract data"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check if required columns exist
            required_columns = ['تاریخ', 'شرح', 'بدهکار', 'بستانکار', 'مانده']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Column '{col}' not found in the transaction file")
            
            return df
        except Exception as e:
            raise Exception(f"Error parsing transaction file: {str(e)}")
    
    @staticmethod
    def extract_option_transactions(df):
        """Extract option transactions from dataframe"""
        option_transactions = []
        
        # Regular expressions for matching option transactions
        buy_pattern = re.compile(r'خرید\s+(\d+)\s+سهم\s+(ض|ط)هرم(\d+)\s+به\s+نرخ\s+(\d+)')
        sell_pattern = re.compile(r'فروش\s+(\d+)\s+سهم\s+(ض|ط)هرم(\d+)\s+به\s+نرخ\s+(\d+)')
        
        for index, row in df.iterrows():
            description = row['شرح']
            date = row['تاریخ']
            debit = row['بدهکار']
            credit = row['بستانکار']
            
            # Check if this is a buy transaction
            buy_match = buy_pattern.search(description)
            if buy_match:
                quantity = int(buy_match.group(1))
                option_type = 'Call' if buy_match.group(2) == 'ض' else 'Put'
                strike_code = buy_match.group(3)
                price = float(buy_match.group(4))
                
                transaction = {
                    'date': date,
                    'action': 'Buy',
                    'symbol': f"{'ض' if option_type == 'Call' else 'ط'}هرم{strike_code}",
                    'option_type': option_type,
                    'strike_code': strike_code,
                    'quantity': quantity,
                    'price': price,
                    'amount': debit
                }
                option_transactions.append(transaction)
                continue
            
            # Check if this is a sell transaction
            sell_match = sell_pattern.search(description)
            if sell_match:
                quantity = int(sell_match.group(1))
                option_type = 'Call' if sell_match.group(2) == 'ض' else 'Put'
                strike_code = sell_match.group(3)
                price = float(sell_match.group(4))
                
                transaction = {
                    'date': date,
                    'action': 'Sell',
                    'symbol': f"{'ض' if option_type == 'Call' else 'ط'}هرم{strike_code}",
                    'option_type': option_type,
                    'strike_code': strike_code,
                    'quantity': quantity,
                    'price': price,
                    'amount': credit
                }
                option_transactions.append(transaction)
        
        return option_transactions
    
    @staticmethod
    def calculate_positions(transactions):
        """Calculate current positions based on transactions"""
        positions = {}
        
        for transaction in transactions:
            symbol = transaction['symbol']
            quantity = transaction['quantity']
            action = transaction['action']
            
            if symbol not in positions:
                positions[symbol] = {
                    'symbol': symbol,
                    'option_type': transaction['option_type'],
                    'strike_code': transaction['strike_code'],
                    'quantity': 0,
                    'avg_price': 0,
                    'total_cost': 0
                }
            
            position = positions[symbol]
            
            if action == 'Buy':
                # Update average price and total cost for buys
                current_quantity = position['quantity']
                current_cost = position['total_cost']
                
                new_quantity = current_quantity + quantity
                new_cost = current_cost + (quantity * transaction['price'])
                
                position['quantity'] = new_quantity
                position['total_cost'] = new_cost
                position['avg_price'] = new_cost / new_quantity if new_quantity > 0 else 0
                
            elif action == 'Sell':
                # Reduce quantity for sells
                position['quantity'] -= quantity
        
        # Filter out closed positions (quantity = 0)
        open_positions = {k: v for k, v in positions.items() if v['quantity'] != 0}
        
        # Convert to list of positions
        position_list = []
        for symbol, position in open_positions.items():
            # Determine position type (long/short)
            position_type = 'Long' if position['quantity'] > 0 else 'Short'
            
            # Convert strike code to actual strike price (simplified mapping)
            # This would need to be adjusted based on actual strike price mapping
            strike_mapping = {
                '0119': 24000,
                '0120': 26000,
                '0121': 28000,
                '0122': 30000,
                '2018': 18000
                # Add more mappings as needed
            }
            
            strike_price = strike_mapping.get(position['strike_code'], 25000)  # Default if not found
            
            position_entry = {
                'type': position['option_type'],
                'position': position_type,
                'strike': strike_price,
                'quantity': abs(position['quantity']),
                'premium': position['avg_price'],
                'symbol': position['symbol']
            }
            position_list.append(position_entry)
        
        return position_list


class TransactionImportWidget(QWidget):
    """Widget for importing and analyzing transaction files"""
    
    def __init__(self, parent=None, position_table=None):
        super(TransactionImportWidget, self).__init__(parent)
        self.position_table = position_table
        self.transactions = []
        self.positions = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        
        # File selection group
        file_group = QGroupBox("Import Transaction File")
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_button)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Options group
        options_group = QGroupBox("Import Options")
        options_layout = QFormLayout()
        
        self.strike_mapping_combo = QComboBox()
        self.strike_mapping_combo.addItems(["Default Mapping", "Custom Mapping"])
        
        self.clear_existing_check = QCheckBox("Clear existing positions")
        self.clear_existing_check.setChecked(True)
        
        options_layout.addRow("Strike Price Mapping:", self.strike_mapping_combo)
        options_layout.addRow("", self.clear_existing_check)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels(['Date', 'Action', 'Symbol', 'Type', 'Quantity', 'Price', 'Amount'])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transactions_table.setAlternatingRowColors(True)
        
        main_layout.addWidget(QLabel("Transactions:"))
        main_layout.addWidget(self.transactions_table)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(6)
        self.positions_table.setHorizontalHeaderLabels(['Symbol', 'Type', 'Position', 'Strike', 'Quantity', 'Avg Price'])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setAlternatingRowColors(True)
        
        main_layout.addWidget(QLabel("Detected Positions:"))
        main_layout.addWidget(self.positions_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        import_button = QPushButton("Import Positions")
        import_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        import_button.clicked.connect(self.import_positions)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(import_button)
        
        main_layout.addLayout(buttons_layout)
    
    def browse_file(self):
        """Open file dialog to select transaction file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transaction File", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.file_path_label.setText(os.path.basename(file_path))
            self.file_path_label.setStyleSheet("color: black; font-style: normal;")
            
            try:
                # Parse the file
                df = TransactionAnalyzer.parse_transaction_file(file_path)
                
                # Extract option transactions
                self.transactions = TransactionAnalyzer.extract_option_transactions(df)
                
                # Calculate positions
                self.positions = TransactionAnalyzer.calculate_positions(self.transactions)
                
                # Update tables
                self.update_transactions_table()
                self.update_positions_table()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def update_transactions_table(self):
        """Update the transactions table with parsed data"""
        self.transactions_table.setRowCount(0)
        
        for transaction in self.transactions:
            row_position = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_position)
            
            self.transactions_table.setItem(row_position, 0, QTableWidgetItem(str(transaction['date'])))
            self.transactions_table.setItem(row_position, 1, QTableWidgetItem(transaction['action']))
            self.transactions_table.setItem(row_position, 2, QTableWidgetItem(transaction['symbol']))
            self.transactions_table.setItem(row_position, 3, QTableWidgetItem(transaction['option_type']))
            self.transactions_table.setItem(row_position, 4, QTableWidgetItem(str(transaction['quantity'])))
            self.transactions_table.setItem(row_position, 5, QTableWidgetItem(str(transaction['price'])))
            self.transactions_table.setItem(row_position, 6, QTableWidgetItem(str(transaction['amount'])))
    
    def update_positions_table(self):
        """Update the positions table with calculated positions"""
        self.positions_table.setRowCount(0)
        
        for position in self.positions:
            row_position = self.positions_table.rowCount()
            self.positions_table.insertRow(row_position)
            
            self.positions_table.setItem(row_position, 0, QTableWidgetItem(position['symbol']))
            self.positions_table.setItem(row_position, 1, QTableWidgetItem(position['type']))
            self.positions_table.setItem(row_position, 2, QTableWidgetItem(position['position']))
            self.positions_table.setItem(row_position, 3, QTableWidgetItem(str(position['strike'])))
            self.positions_table.setItem(row_position, 4, QTableWidgetItem(str(position['quantity'])))
            self.positions_table.setItem(row_position, 5, QTableWidgetItem(str(position['premium'])))
    
    def import_positions(self):
        """Import detected positions to the main position table"""
        if not self.positions:
            QMessageBox.warning(self, "No Positions", "No positions detected to import.")
            return
        
        if not self.position_table:
            QMessageBox.critical(self, "Error", "Position table reference not set.")
            return
        
        # Clear existing positions if checked
        if self.clear_existing_check.isChecked():
            self.position_table.clear_all_positions()
        
        # Add positions to the main table
        for position in self.positions:
            self.position_table.add_position(
                position['type'],
                position['position'],
                position['strike'],
                position['quantity'],
                position['premium']
            )
        
        QMessageBox.information(self, "Success", f"Successfully imported {len(self.positions)} positions.")
        self.close()
