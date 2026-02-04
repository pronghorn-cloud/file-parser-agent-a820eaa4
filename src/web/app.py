"""Flask web application for File Parser Agent.

Provides a web UI for:
- File upload
- Parsing documents
- Viewing and downloading results
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify
)
from werkzeug.utils import secure_filename

from ..api.wrapper import FileParserAgent
from ..config import (
    UPLOADS_DIR,
    OUTPUTS_DIR,
    MAX_FILE_SIZE_BYTES,
    ALL_SUPPORTED_EXTENSIONS,
    OUTPUT_FORMATS
)


def create_app(config: dict = None) -> Flask:
    """Create Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask app
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / 'templates'),
        static_folder=str(Path(__file__).parent / 'static')
    )
    
    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        MAX_CONTENT_LENGTH=MAX_FILE_SIZE_BYTES,
        UPLOAD_FOLDER=str(UPLOADS_DIR),
        OUTPUT_FOLDER=str(OUTPUTS_DIR),
        ANTHROPIC_API_KEY=os.environ.get('ANTHROPIC_API_KEY', ''),
    )
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    # Ensure directories exist
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize agent
    agent = FileParserAgent(
        output_dir=Path(app.config['OUTPUT_FOLDER']),
        enable_vision=bool(app.config['ANTHROPIC_API_KEY']),
        anthropic_api_key=app.config['ANTHROPIC_API_KEY']
    )
    
    # Store agent in app context
    app.agent = agent
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app: Flask):
    """Register application routes."""
    
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        if '.' not in filename:
            return False
        ext = '.' + filename.rsplit('.', 1)[1].lower()
        return ext in ALL_SUPPORTED_EXTENSIONS
    
    @app.route('/')
    def index():
        """Main page with upload form."""
        return render_template(
            'index.html',
            supported_extensions=ALL_SUPPORTED_EXTENSIONS,
            output_formats=OUTPUT_FORMATS,
            max_size_mb=MAX_FILE_SIZE_BYTES / (1024 * 1024)
        )
    
    @app.route('/upload', methods=['POST'])
    def upload():
        """Handle file upload and parsing."""
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash(f'Unsupported file type. Allowed: {ALL_SUPPORTED_EXTENSIONS}', 'error')
            return redirect(url_for('index'))
        
        # Get options
        output_format = request.form.get('format', 'json')
        analyze_images = request.form.get('analyze_images') == 'on'
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        upload_path = Path(app.config['UPLOAD_FOLDER']) / unique_filename
        
        try:
            file.save(str(upload_path))
            
            # Parse document
            result = app.agent.parse_and_save(
                upload_path,
                output_format=output_format,
                analyze_images=analyze_images
            )
            
            # Clean up upload
            upload_path.unlink(missing_ok=True)
            
            flash(f'File parsed successfully!', 'success')
            return redirect(url_for(
                'result',
                filename=Path(result['output_path']).name
            ))
            
        except Exception as e:
            # Clean up on error
            upload_path.unlink(missing_ok=True)
            flash(f'Error parsing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/result/<filename>')
    def result(filename: str):
        """Display parsing result."""
        output_path = app.agent.get_output(filename)
        
        if not output_path:
            flash('Output file not found', 'error')
            return redirect(url_for('index'))
        
        # Read file content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine display type
        file_ext = Path(filename).suffix.lower()
        is_json = file_ext == '.json'
        is_markdown = file_ext == '.md'
        
        return render_template(
            'result.html',
            filename=filename,
            content=content,
            is_json=is_json,
            is_markdown=is_markdown
        )
    
    @app.route('/download/<filename>')
    def download(filename: str):
        """Download output file."""
        output_path = app.agent.get_output(filename)
        
        if not output_path:
            flash('File not found', 'error')
            return redirect(url_for('index'))
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename
        )
    
    @app.route('/outputs')
    def outputs():
        """List all output files."""
        files = app.agent.list_outputs()
        return render_template('outputs.html', files=files)
    
    @app.route('/delete/<filename>', methods=['POST'])
    def delete(filename: str):
        """Delete an output file."""
        if app.agent.delete_output(filename):
            flash(f'Deleted: {filename}', 'success')
        else:
            flash('File not found', 'error')
        return redirect(url_for('outputs'))
    
    @app.route('/clear', methods=['POST'])
    def clear():
        """Clear all outputs."""
        count = app.agent.clear_outputs()
        flash(f'Deleted {count} files', 'success')
        return redirect(url_for('outputs'))
    
    # API endpoints for programmatic access
    @app.route('/api/parse', methods=['POST'])
    def api_parse():
        """API endpoint for parsing."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Get options from JSON body or form
        analyze_images = request.form.get('analyze_images', 'true').lower() == 'true'
        
        # Save and parse
        filename = secure_filename(file.filename)
        upload_path = Path(app.config['UPLOAD_FOLDER']) / f"api_{filename}"
        
        try:
            file.save(str(upload_path))
            result = app.agent.parse_document(upload_path, analyze_images)
            upload_path.unlink(missing_ok=True)
            return jsonify(result)
            
        except Exception as e:
            upload_path.unlink(missing_ok=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/outputs')
    def api_outputs():
        """API endpoint for listing outputs."""
        return jsonify(app.agent.list_outputs())
    
    @app.route('/api/formats')
    def api_formats():
        """API endpoint for supported formats."""
        return jsonify(app.agent.get_supported_formats())
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file too large error."""
        flash(f'File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB', 'error')
        return redirect(url_for('index'))
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle server error."""
        return render_template('error.html', error=str(e)), 500


# Create default app instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
