#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.stats import norm
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTabWidget, QComboBox, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
                            QFileDialog, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QRadioButton, QButtonGroup, QSplitter, QFrame,
                            QScrollArea, QSizePolicy, QGridLayout, QAction, QMenu, QToolBar,
                            QDialog)
from PyQt5.QtCore import Qt, QSize, QSettings, QTimer, QDate, QDateTime
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap

# Import custom modules
from options_charts import OptionsChartGenerator
from transaction_import import TransactionImportWidget

class OptionsCalculator:
    """Class for options pricing and Greeks calculations"""
    
    @staticmethod
    def black_scholes_price(S, K, T, r, sigma, option_type='call'):
        """Calculate option price using Black-Scholes model"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # Put option
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        return price
    
    @staticmethod
    def calculate_delta(S, K, T, r, sigma, option_type='call'):
        """Calculate option delta"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() == 'call':
            delta = norm.cdf(d1)
        else:  # Put option
            delta = norm.cdf(d1) - 1
            
        return delta
    
    @staticmethod
    def calculate_gamma(S, K, T, r, sigma):
        """Calculate option gamma (same for call and put)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return gamma
    
    @staticmethod
    def calculate_theta(S, K, T, r, sigma, option_type='call'):
        """Calculate option theta"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            theta = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:  # Put option
            theta = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)
            
        # Convert from yearly to daily theta
        theta = theta / 365
        return theta
    
    @staticmethod
    def calculate_vega(S, K, T, r, sigma):
        """Calculate option vega (same for call and put)"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        vega = S * np.sqrt(T) * norm.pdf(d1) / 100  # Divided by 100 to get change per 1% move in IV
        return vega
    
    @staticmethod
    def calculate_rho(S, K, T, r, sigma, option_type='call'):
        """Calculate option rho"""
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:  # Put option
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
            
        return rho
    
    @staticmethod
    def calculate_all_greeks(S, K, T, r, sigma, option_type='call'):
        """Calculate all option Greeks at once"""
        price = OptionsCalculator.black_scholes_price(S, K, T, r, sigma, option_type)
        delta = OptionsCalculator.calculate_delta(S, K, T, r, sigma, option_type)
        gamma = OptionsCalculator.calculate_gamma(S, K, T, r, sigma)
        theta = OptionsCalculator.calculate_theta(S, K, T, r, sigma, option_type)
        vega = OptionsCalculator.calculate_vega(S, K, T, r, sigma)
        rho = OptionsCalculator.calculate_rho(S, K, T, r, sigma, option_type)
        
        return {
            'price': price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }


class StrategyCalculator:
    """Class for calculating strategy P&L and Greeks"""
    
    @staticmethod
    def calculate_strategy_metrics(positions, S_range, current_price, days_to_expiry, risk_free_rate, implied_volatility):
        """
        Calculate P&L and Greeks for a strategy across a range of prices
        
        Parameters:
        positions - list of dictionaries with position details
        S_range - array of stock prices to calculate metrics for
        current_price - current stock price
        days_to_expiry - days to expiration
        risk_free_rate - annual risk-free rate
        implied_volatility - implied volatility
        
        Returns:
        Dictionary with arrays for P&L and Greeks across S_range
        """
        T = days_to_expiry / 365  # Convert days to years
        
        # Initialize arrays for strategy metrics
        strategy_pnl = np.zeros_like(S_range, dtype=float)
        strategy_delta = np.zeros_like(S_range, dtype=float)
        strategy_gamma = np.zeros_like(S_range, dtype=float)
        strategy_theta = np.zeros_like(S_range, dtype=float)
        strategy_vega = np.zeros_like(S_range, dtype=float)
        
        # Calculate initial option prices at current stock price
        initial_prices = {}
        for i, position in enumerate(positions):
            option_type = position['type'].lower()
            strike = position['strike']
            initial_prices[i] = OptionsCalculator.black_scholes_price(
                current_price, strike, T, risk_free_rate, implied_volatility, option_type
            )
        
        # Calculate metrics for each price in the range
        for i, S in enumerate(S_range):
            for j, position in enumerate(positions):
                option_type = position['type'].lower()
                strike = position['strike']
                quantity = position['quantity']
                is_long = position['position'] == 'long'
                multiplier = 1 if is_long else -1
                
                # Calculate option price at this stock price
                option_price = OptionsCalculator.black_scholes_price(
                    S, strike, T, risk_free_rate, implied_volatility, option_type
                )
                
                # Calculate P&L (current price - initial price) * quantity * multiplier
                position_pnl = (option_price - initial_prices[j]) * quantity * multiplier
                strategy_pnl[i] += position_pnl
                
                # Calculate Greeks
                greeks = OptionsCalculator.calculate_all_greeks(
                    S, strike, T, risk_free_rate, implied_volatility, option_type
                )
                
                strategy_delta[i] += greeks['delta'] * quantity * multiplier
                strategy_gamma[i] += greeks['gamma'] * quantity * multiplier
                strategy_theta[i] += greeks['theta'] * quantity * multiplier
                strategy_vega[i] += greeks['vega'] * quantity * multiplier
        
        return {
            'price_range': S_range,
            'pnl': strategy_pnl,
            'delta': strategy_delta,
            'gamma': strategy_gamma,
            'theta': strategy_theta,
            'vega': strategy_vega
        }


class MatplotlibCanvas(FigureCanvas):
    """Matplotlib canvas for embedding plots in PyQt"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class PositionTableWidget(QTableWidget):
    """Custom table widget for managing option positions"""
    
    def __init__(self, parent=None):
        super(PositionTableWidget, self).__init__(parent)
        
        # Set up the table
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['Type', 'Position', 'Strike', 'Quantity', 'Premium', 'Actions'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        
        # Style the table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
    def add_position(self, option_type, position_type, strike, quantity, premium):
        """Add a new position to the table"""
        row_position = self.rowCount()
        self.insertRow(row_position)
        
        # Add data to the table
        self.setItem(row_position, 0, QTableWidgetItem(option_type))
        self.setItem(row_position, 1, QTableWidgetItem(position_type))
        self.setItem(row_position, 2, QTableWidgetItem(str(strike)))
        self.setItem(row_position, 3, QTableWidgetItem(str(quantity)))
        self.setItem(row_position, 4, QTableWidgetItem(str(premium)))
        
        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet("background-color: #f44336; color: white;")
        delete_button.clicked.connect(lambda: self.remove_position(row_position))
        self.setCellWidget(row_position, 5, delete_button)
        
    def remove_position(self, row):
        """Remove a position from the table"""
        self.removeRow(row)
        
    def get_all_positions(self):
        """Get all positions from the table as a list of dictionaries"""
        positions = []
        for row in range(self.rowCount()):
            position = {
                'type': self.item(row, 0).text(),
                'position': self.item(row, 1).text(),
                'strike': float(self.item(row, 2).text()),
                'quantity': int(self.item(row, 3).text()),
                'premium': float(self.item(row, 4).text())
            }
            positions.append(position)
        return positions
    
    def clear_all_positions(self):
        """Clear all positions from the table"""
        self.setRowCount(0)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # Set up the main window
        self.setWindowTitle("Options Strategy Analyzer")
        self.setMinimumSize(1200, 800)
        
        # Set up the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Create the main UI components
        self.create_input_panel()
        self.create_position_table()
        self.create_chart_tabs()
        
        # Set up the main layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top panel (inputs and position table)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(self.input_panel)
        top_layout.addWidget(self.position_group)
        main_splitter.addWidget(top_widget)
        
        # Bottom panel (charts)
        main_splitter.addWidget(self.chart_tabs)
        
        # Set initial sizes
        main_splitter.setSizes([300, 500])
        
        # Add the splitter to the main layout
        self.main_layout.addWidget(main_splitter)
        
        # Set the application style
        self.set_application_style()
        
        # Initialize variables
        self.current_strategy_metrics = None
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # New strategy action
        new_action = QAction('New Strategy', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_strategy)
        file_menu.addAction(new_action)
        
        # Save strategy action
        save_action = QAction('Save Strategy', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_strategy)
        file_menu.addAction(save_action)
        
        # Load strategy action
        load_action = QAction('Load Strategy', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_strategy)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Import transactions action
        import_action = QAction('Import Transactions', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_transactions)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Export charts action
        export_action = QAction('Export Charts', self)
        export_action.triggered.connect(self.export_charts)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        # Calculate metrics action
        calc_action = QAction('Calculate Strategy Metrics', self)
        calc_action.setShortcut('F5')
        calc_action.triggered.connect(self.calculate_strategy)
        tools_menu.addAction(calc_action)
        
        # Clear all action
        clear_action = QAction('Clear All Positions', self)
        clear_action.triggered.connect(self.clear_all_positions)
        tools_menu.addAction(clear_action)
        
        # Advanced charts submenu
        advanced_menu = tools_menu.addMenu('Advanced Charts')
        
        # Gamma surface action
        gamma_surface_action = QAction('Gamma Surface', self)
        gamma_surface_action.triggered.connect(self.show_gamma_surface)
        advanced_menu.addAction(gamma_surface_action)
        
        # Gamma/Theta ratio action
        gamma_theta_action = QAction('Gamma/Theta Ratio', self)
        gamma_theta_action.triggered.connect(self.show_gamma_theta_ratio)
        advanced_menu.addAction(gamma_theta_action)
        
        # All Greeks comparison action
        all_greeks_action = QAction('All Greeks Comparison', self)
        all_greeks_action.triggered.connect(self.show_all_greeks_comparison)
        advanced_menu.addAction(all_greeks_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def create_input_panel(self):
        """Create the input panel for strategy parameters"""
        self.input_panel = QGroupBox("Strategy Parameters")
        input_layout = QHBoxLayout()
        
        # Left form layout
        left_form = QFormLayout()
        
        # Underlying price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(1, 1000000)
        self.price_input.setValue(25990)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(100)
        left_form.addRow("Underlying Price:", self.price_input)
        
        # Risk-free rate
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 1)
        self.rate_input.setValue(0.2)
        self.rate_input.setDecimals(4)
        self.rate_input.setSingleStep(0.01)
        left_form.addRow("Risk-Free Rate:", self.rate_input)
        
        # Right form layout
        right_form = QFormLayout()
        
        # Days to expiry
        self.days_input = QSpinBox()
        self.days_input.setRange(1, 1000)
        self.days_input.setValue(5)
        right_form.addRow("Days to Expiry:", self.days_input)
        
        # Implied volatility
        self.volatility_input = QDoubleSpinBox()
        self.volatility_input.setRange(0.01, 2)
        self.volatility_input.setValue(0.69)
        self.volatility_input.setDecimals(2)
        self.volatility_input.setSingleStep(0.01)
        right_form.addRow("Implied Volatility:", self.volatility_input)
        
        # Add forms to the input layout
        input_layout.addLayout(left_form)
        input_layout.addLayout(right_form)
        
        # Add calculate button
        calc_button = QPushButton("Calculate")
        calc_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        calc_button.clicked.connect(self.calculate_strategy)
        input_layout.addWidget(calc_button)
        
        self.input_panel.setLayout(input_layout)
        
    def create_position_table(self):
        """Create the position table and add position form"""
        self.position_group = QGroupBox("Option Positions")
        position_layout = QVBoxLayout()
        
        # Add position form
        add_form = QHBoxLayout()
        
        # Option type
        self.option_type_combo = QComboBox()
        self.option_type_combo.addItems(["Call", "Put"])
        add_form.addWidget(QLabel("Type:"))
        add_form.addWidget(self.option_type_combo)
        
        # Position type
        self.position_type_combo = QComboBox()
        self.position_type_combo.addItems(["Long", "Short"])
        add_form.addWidget(QLabel("Position:"))
        add_form.addWidget(self.position_type_combo)
        
        # Strike price
        self.strike_input = QDoubleSpinBox()
        self.strike_input.setRange(1, 1000000)
        self.strike_input.setValue(26000)
        self.strike_input.setDecimals(2)
        self.strike_input.setSingleStep(1000)
        add_form.addWidget(QLabel("Strike:"))
        add_form.addWidget(self.strike_input)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        add_form.addWidget(QLabel("Quantity:"))
        add_form.addWidget(self.quantity_input)
        
        # Premium
        self.premium_input = QDoubleSpinBox()
        self.premium_input.setRange(0.01, 1000000)
        self.premium_input.setValue(1500)
        self.premium_input.setDecimals(2)
        self.premium_input.setSingleStep(100)
        add_form.addWidget(QLabel("Premium:"))
        add_form.addWidget(self.premium_input)
        
        # Add button
        add_button = QPushButton("Add Position")
        add_button.setStyleSheet("background-color: #2196F3; color: white;")
        add_button.clicked.connect(self.add_position)
        add_form.addWidget(add_button)
        
        # Import button
        import_button = QPushButton("Import")
        import_button.setStyleSheet("background-color: #FF9800; color: white;")
        import_button.clicked.connect(self.import_transactions)
        add_form.addWidget(import_button)
        
        # Position table
        self.position_table = PositionTableWidget()
        
        # Add widgets to layout
        position_layout.addLayout(add_form)
        position_layout.addWidget(self.position_table)
        
        self.position_group.setLayout(position_layout)
        
    def create_chart_tabs(self):
        """Create the chart tabs for different visualizations"""
        self.chart_tabs = QTabWidget()
        
        # P&L chart tab
        self.pnl_tab = QWidget()
        pnl_layout = QVBoxLayout(self.pnl_tab)
        self.pnl_canvas = MatplotlibCanvas(self.pnl_tab, width=5, height=4, dpi=100)
        self.pnl_toolbar = NavigationToolbar(self.pnl_canvas, self.pnl_tab)
        pnl_layout.addWidget(self.pnl_toolbar)
        pnl_layout.addWidget(self.pnl_canvas)
        self.chart_tabs.addTab(self.pnl_tab, "Profit/Loss")
        
        # Greeks tabs
        # Delta
        self.delta_tab = QWidget()
        delta_layout = QVBoxLayout(self.delta_tab)
        self.delta_canvas = MatplotlibCanvas(self.delta_tab, width=5, height=4, dpi=100)
        self.delta_toolbar = NavigationToolbar(self.delta_canvas, self.delta_tab)
        delta_layout.addWidget(self.delta_toolbar)
        delta_layout.addWidget(self.delta_canvas)
        self.chart_tabs.addTab(self.delta_tab, "Delta")
        
        # Gamma
        self.gamma_tab = QWidget()
        gamma_layout = QVBoxLayout(self.gamma_tab)
        self.gamma_canvas = MatplotlibCanvas(self.gamma_tab, width=5, height=4, dpi=100)
        self.gamma_toolbar = NavigationToolbar(self.gamma_canvas, self.gamma_tab)
        gamma_layout.addWidget(self.gamma_toolbar)
        gamma_layout.addWidget(self.gamma_canvas)
        self.chart_tabs.addTab(self.gamma_tab, "Gamma")
        
        # Theta
        self.theta_tab = QWidget()
        theta_layout = QVBoxLayout(self.theta_tab)
        self.theta_canvas = MatplotlibCanvas(self.theta_tab, width=5, height=4, dpi=100)
        self.theta_toolbar = NavigationToolbar(self.theta_canvas, self.theta_tab)
        theta_layout.addWidget(self.theta_toolbar)
        theta_layout.addWidget(self.theta_canvas)
        self.chart_tabs.addTab(self.theta_tab, "Theta")
        
        # Vega
        self.vega_tab = QWidget()
        vega_layout = QVBoxLayout(self.vega_tab)
        self.vega_canvas = MatplotlibCanvas(self.vega_tab, width=5, height=4, dpi=100)
        self.vega_toolbar = NavigationToolbar(self.vega_canvas, self.vega_tab)
        vega_layout.addWidget(self.vega_toolbar)
        vega_layout.addWidget(self.vega_canvas)
        self.chart_tabs.addTab(self.vega_tab, "Vega")
        
    def set_application_style(self):
        """Set the application style and theme"""
        # Set font
        app_font = QFont("Segoe UI", 9)
        QApplication.setFont(app_font)
        
        # Set stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #d0d0d0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom-color: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #f5f5f5;
                border-bottom-color: #f5f5f5;
            }
            QTabBar::tab:hover {
                background-color: #eaeaea;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
        
    def add_position(self):
        """Add a new position to the table"""
        option_type = self.option_type_combo.currentText()
        position_type = self.position_type_combo.currentText().lower()
        strike = self.strike_input.value()
        quantity = self.quantity_input.value()
        premium = self.premium_input.value()
        
        self.position_table.add_position(option_type, position_type, strike, quantity, premium)
        
    def calculate_strategy(self):
        """Calculate and display strategy metrics"""
        # Get positions from the table
        positions = self.position_table.get_all_positions()
        
        if not positions:
            QMessageBox.warning(self, "No Positions", "Please add at least one option position.")
            return
        
        # Get parameters
        current_price = self.price_input.value()
        days_to_expiry = self.days_input.value()
        risk_free_rate = self.rate_input.value()
        implied_volatility = self.volatility_input.value()
        
        # Create price range (±30% from current price)
        price_min = current_price * 0.7
        price_max = current_price * 1.3
        S_range = np.linspace(price_min, price_max, 1000)
        
        # Calculate strategy metrics
        self.current_strategy_metrics = StrategyCalculator.calculate_strategy_metrics(
            positions, S_range, current_price, days_to_expiry, risk_free_rate, implied_volatility
        )
        
        # Update charts
        self.update_charts()
        
    def update_charts(self):
        """Update all charts with current strategy metrics"""
        if not self.current_strategy_metrics:
            return
        
        # Get data
        price_range = self.current_strategy_metrics['price_range']
        pnl = self.current_strategy_metrics['pnl']
        delta = self.current_strategy_metrics['delta']
        gamma = self.current_strategy_metrics['gamma']
        theta = self.current_strategy_metrics['theta']
        vega = self.current_strategy_metrics['vega']
        
        current_price = self.price_input.value()
        
        # Update P&L chart using the chart generator
        self.pnl_canvas.axes.clear()
        fig = OptionsChartGenerator.generate_pnl_chart(price_range, pnl, current_price)
        self.pnl_canvas.axes = fig.gca()
        self.pnl_canvas.draw()
        
        # Update Delta chart
        self.delta_canvas.axes.clear()
        fig = OptionsChartGenerator.generate_greek_chart(price_range, delta, current_price, "Delta", 'g')
        self.delta_canvas.axes = fig.gca()
        self.delta_canvas.draw()
        
        # Update Gamma chart
        self.gamma_canvas.axes.clear()
        fig = OptionsChartGenerator.generate_greek_chart(price_range, gamma, current_price, "Gamma", 'r')
        self.gamma_canvas.axes = fig.gca()
        self.gamma_canvas.draw()
        
        # Update Theta chart
        self.theta_canvas.axes.clear()
        fig = OptionsChartGenerator.generate_greek_chart(price_range, theta, current_price, "Theta", 'c')
        self.theta_canvas.axes = fig.gca()
        self.theta_canvas.draw()
        
        # Update Vega chart
        self.vega_canvas.axes.clear()
        fig = OptionsChartGenerator.generate_greek_chart(price_range, vega, current_price, "Vega", 'm')
        self.vega_canvas.axes = fig.gca()
        self.vega_canvas.draw()
        
    def new_strategy(self):
        """Create a new strategy (clear all inputs and positions)"""
        reply = QMessageBox.question(self, 'New Strategy', 
                                     'Are you sure you want to create a new strategy? All current data will be lost.',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.clear_all_positions()
            self.price_input.setValue(25990)
            self.rate_input.setValue(0.2)
            self.days_input.setValue(5)
            self.volatility_input.setValue(0.69)
            self.current_strategy_metrics = None
            
            # Clear charts
            for canvas in [self.pnl_canvas, self.delta_canvas, self.gamma_canvas, 
                          self.theta_canvas, self.vega_canvas]:
                canvas.axes.clear()
                canvas.draw()
        
    def save_strategy(self):
        """Save the current strategy to a file"""
        if not self.position_table.get_all_positions():
            QMessageBox.warning(self, "No Positions", "There are no positions to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Strategy", "", "JSON Files (*.json)")
        
        if file_path:
            # If the user didn't add .json extension, add it
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            strategy_data = {
                'parameters': {
                    'price': self.price_input.value(),
                    'rate': self.rate_input.value(),
                    'days': self.days_input.value(),
                    'volatility': self.volatility_input.value()
                },
                'positions': self.position_table.get_all_positions()
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(strategy_data, f, indent=4)
                QMessageBox.information(self, "Success", "Strategy saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save strategy: {str(e)}")
        
    def load_strategy(self):
        """Load a strategy from a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Strategy", "", "JSON Files (*.json)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    strategy_data = json.load(f)
                
                # Load parameters
                parameters = strategy_data.get('parameters', {})
                self.price_input.setValue(parameters.get('price', 25990))
                self.rate_input.setValue(parameters.get('rate', 0.2))
                self.days_input.setValue(parameters.get('days', 5))
                self.volatility_input.setValue(parameters.get('volatility', 0.69))
                
                # Load positions
                self.position_table.clear_all_positions()
                for position in strategy_data.get('positions', []):
                    self.position_table.add_position(
                        position['type'],
                        position['position'],
                        position['strike'],
                        position['quantity'],
                        position['premium']
                    )
                
                QMessageBox.information(self, "Success", "Strategy loaded successfully.")
                
                # Calculate strategy metrics
                self.calculate_strategy()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load strategy: {str(e)}")
    
    def import_transactions(self):
        """Open the transaction import dialog"""
        import_dialog = QDialog(self)
        import_dialog.setWindowTitle("Import Transactions")
        import_dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(import_dialog)
        import_widget = TransactionImportWidget(import_dialog, self.position_table)
        layout.addWidget(import_widget)
        
        import_dialog.exec_()
        
    def export_charts(self):
        """Export charts to image files"""
        if not self.current_strategy_metrics:
            QMessageBox.warning(self, "No Data", "Please calculate strategy metrics first.")
            return
        
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Charts")
        
        if directory:
            try:
                # Export P&L chart
                self.pnl_canvas.fig.savefig(os.path.join(directory, "profit_loss_chart.png"), dpi=300, bbox_inches='tight')
                
                # Export Delta chart
                self.delta_canvas.fig.savefig(os.path.join(directory, "delta_chart.png"), dpi=300, bbox_inches='tight')
                
                # Export Gamma chart
                self.gamma_canvas.fig.savefig(os.path.join(directory, "gamma_chart.png"), dpi=300, bbox_inches='tight')
                
                # Export Theta chart
                self.theta_canvas.fig.savefig(os.path.join(directory, "theta_chart.png"), dpi=300, bbox_inches='tight')
                
                # Export Vega chart
                self.vega_canvas.fig.savefig(os.path.join(directory, "vega_chart.png"), dpi=300, bbox_inches='tight')
                
                QMessageBox.information(self, "Success", "Charts exported successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export charts: {str(e)}")
    
    def show_gamma_surface(self):
        """Show the gamma surface chart"""
        if not self.current_strategy_metrics:
            QMessageBox.warning(self, "No Data", "Please calculate strategy metrics first.")
            return
        
        # Create a dialog to display the gamma surface
        dialog = QDialog(self)
        dialog.setWindowTitle("Gamma Surface")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create canvas for the gamma surface
        canvas = MatplotlibCanvas(dialog, width=8, height=6, dpi=100)
        toolbar = NavigationToolbar(canvas, dialog)
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Generate gamma surface data
        current_price = self.price_input.value()
        days_to_expiry = self.days_input.value()
        risk_free_rate = self.rate_input.value()
        implied_volatility = self.volatility_input.value()
        
        # Create strike price range and days range
        strike_prices = np.linspace(current_price * 0.7, current_price * 1.3, 50)
        days_range = np.linspace(1, days_to_expiry * 2, 20)
        
        # Calculate gamma for each combination of strike and days
        gamma_values = np.zeros((len(days_range), len(strike_prices)))
        
        for i, days in enumerate(days_range):
            T = days / 365  # Convert days to years
            for j, K in enumerate(strike_prices):
                gamma_values[i, j] = OptionsCalculator.calculate_gamma(current_price, K, T, risk_free_rate, implied_volatility)
        
        # Generate the gamma surface chart
        fig = OptionsChartGenerator.generate_gamma_surface_chart(strike_prices, days_range, gamma_values)
        canvas.figure = fig
        canvas.draw()
        
        dialog.exec_()
    
    def show_gamma_theta_ratio(self):
        """Show the gamma/theta ratio chart"""
        if not self.current_strategy_metrics:
            QMessageBox.warning(self, "No Data", "Please calculate strategy metrics first.")
            return
        
        # Create a dialog to display the gamma/theta ratio
        dialog = QDialog(self)
        dialog.setWindowTitle("Gamma/Theta Ratio")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create canvas for the ratio chart
        canvas = MatplotlibCanvas(dialog, width=8, height=6, dpi=100)
        toolbar = NavigationToolbar(canvas, dialog)
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Get data from current strategy metrics
        price_range = self.current_strategy_metrics['price_range']
        gamma = self.current_strategy_metrics['gamma']
        theta = self.current_strategy_metrics['theta']
        current_price = self.price_input.value()
        
        # Generate the gamma/theta ratio chart
        fig = OptionsChartGenerator.generate_gamma_to_theta_ratio_chart(price_range, gamma, theta, current_price)
        canvas.figure = fig
        canvas.draw()
        
        dialog.exec_()
    
    def show_all_greeks_comparison(self):
        """Show chart comparing all Greeks"""
        if not self.current_strategy_metrics:
            QMessageBox.warning(self, "No Data", "Please calculate strategy metrics first.")
            return
        
        # Create a dialog to display the comparison chart
        dialog = QDialog(self)
        dialog.setWindowTitle("All Greeks Comparison")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create canvas for the comparison chart
        canvas = MatplotlibCanvas(dialog, width=8, height=6, dpi=100)
        toolbar = NavigationToolbar(canvas, dialog)
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Get data from current strategy metrics
        price_range = self.current_strategy_metrics['price_range']
        delta = self.current_strategy_metrics['delta']
        gamma = self.current_strategy_metrics['gamma']
        theta = self.current_strategy_metrics['theta']
        vega = self.current_strategy_metrics['vega']
        current_price = self.price_input.value()
        
        # Generate the comparison chart
        fig = OptionsChartGenerator.generate_all_greeks_comparison_chart(price_range, delta, gamma, theta, vega, current_price)
        canvas.figure = fig
        canvas.draw()
        
        dialog.exec_()
        
    def clear_all_positions(self):
        """Clear all positions from the table"""
        reply = QMessageBox.question(self, 'Clear Positions', 
                                     'Are you sure you want to clear all positions?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.position_table.clear_all_positions()
        
    def show_about_dialog(self):
        """Show the about dialog"""
        about_text = """
        <h1>Options Strategy Analyzer</h1>
        <p>Version 1.0</p>
        <p>A professional tool for analyzing options trading strategies.</p>
        <p>Features:</p>
        <ul>
            <li>Black-Scholes option pricing</li>
            <li>Greeks calculation (Delta, Gamma, Theta, Vega)</li>
            <li>Strategy P&L visualization</li>
            <li>Transaction file import</li>
            <li>Advanced gamma analysis</li>
            <li>Save and load strategies</li>
            <li>Export charts</li>
        </ul>
        <p>Created for options traders in the Iranian market.</p>
        """
        
        QMessageBox.about(self, "About Options Strategy Analyzer", about_text)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
