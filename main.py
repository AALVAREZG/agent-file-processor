"""
Liquidación OPAEF - Desktop Application
Main entry point for the application.

A desktop tool for extracting and processing liquidation documents from
Diputación Provincial (OPAEF format).
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
