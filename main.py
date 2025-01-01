import tkinter as tk
from src.gui import FlashSortApp
import sys
import os

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    root = tk.Tk()
    # Set icon if available? 
    app = FlashSortApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
