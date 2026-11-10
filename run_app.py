import os
import sys
import webbrowser
from threading import Timer
import streamlit.web.cli as stcli

def resolve_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def open_browser():
    """Opens local browser tab automatically to the Streamlit app."""
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    # Ensure current working directory is executable directory for database persistence
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
        
    app_path = resolve_path("ca_dashboard_app.py")
    
    # Open browser automatically after 1.5 seconds
    Timer(1.5, open_browser).start()
    
    # Run Streamlit CLI programmatically
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.port=8501",
    ]
    sys.exit(stcli.main())
