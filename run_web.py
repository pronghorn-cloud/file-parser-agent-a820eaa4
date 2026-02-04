#!/usr/bin/env python
"""Quick script to run the web server."""

from src.web.app import app

if __name__ == '__main__':
    print("Starting File Parser Agent web server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
