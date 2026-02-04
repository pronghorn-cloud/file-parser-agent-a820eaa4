#!/usr/bin/env python
"""Quick script to run the web server."""

import os
from src.web.app import app

if __name__ == '__main__':
    # Get port from environment variable (Render.com sets this)
    port = int(os.environ.get('PORT', 5000))
    # In production, debug should be False
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting File Parser Agent web server on port {port}...")
    if debug:
        print(f"Open http://localhost:{port} in your browser")
    
    # Bind to 0.0.0.0 for external access (required for Render.com)
    app.run(host='0.0.0.0', port=port, debug=debug)

