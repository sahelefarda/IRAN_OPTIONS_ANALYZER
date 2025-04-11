#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from options_analyzer import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

def main():
    app = QApplication(sys.argv)
    
    # Set application icon if available
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
