"""AI Vision service for image and chart analysis."""

import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from ..config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_IMAGE_SIZE_BYTES

logger = logging.getLogger(__name__)


class VisionService:
    """AI-powered image and chart analysis service.
    
    Uses Anthropic Claude API for vision tasks:
    - Image description
    - Chart analysis
    - Diagram interpretation
    """
    
    def __init__(self, api_key: str = None):
        """Initialize vision service.
        
        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic SDK is required. Install with: pip install anthropic")
        
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            logger.warning("No Anthropic API key configured. Vision features will be disabled.")
            self._client = None
        else:
            self._client = Anthropic(api_key=self.api_key)
        
        self.model = CLAUDE_MODEL
    
    @property
    def is_available(self) -> bool:
        """Check if vision service is available."""
        return self._client is not None
    
    def analyze_image(
        self,
        image_data: bytes,
        content_type: str = 'image/png',
        prompt: str = None
    ) -> Dict[str, Any]:
        """Analyze an image using AI vision.
        
        Args:
            image_data: Raw image bytes
            content_type: MIME type of image
            prompt: Custom prompt for analysis
            
        Returns:
            Analysis result with description
        """
        if not self.is_available:
            return {
                'success': False,
                'error': 'Vision service not configured (missing API key)'
            }
        
        # Compress image if needed
        image_data = self._compress_if_needed(image_data, content_type)
        
        # Encode to base64
        image_b64 = base64.standard_b64encode(image_data).decode('utf-8')
        
        # Default prompt for general analysis
        if not prompt:
            prompt = """Analyze this image and provide a detailed description. Include:
1. What type of image this is (photo, chart, diagram, etc.)
2. The main content and key elements
3. Any text visible in the image
4. If it's a chart/graph: the type, data trends, and key insights
5. If it's a diagram: the structure and relationships shown

Provide a clear, concise description suitable for accessibility purposes."""
        
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": content_type,
                                    "data": image_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            description = response.content[0].text if response.content else ""
            
            return {
                'success': True,
                'description': description,
                'model': self.model,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_chart(
        self,
        image_data: bytes,
        content_type: str = 'image/png',
        chart_type: str = None
    ) -> Dict[str, Any]:
        """Specialized analysis for charts and graphs.
        
        Args:
            image_data: Raw image bytes
            content_type: MIME type
            chart_type: Hint about chart type if known
            
        Returns:
            Chart analysis with data insights
        """
        prompt = f"""Analyze this {'chart' if not chart_type else chart_type} and provide:

1. **Chart Type**: What kind of visualization is this?
2. **Title/Labels**: What is the chart titled? What are the axis labels?
3. **Data Summary**: Summarize the key data points or values shown
4. **Trends**: What trends or patterns are visible?
5. **Key Insights**: What are the main takeaways from this chart?

Be specific about any numbers, percentages, or values you can discern."""
        
        return self.analyze_image(image_data, content_type, prompt)
    
    def describe_for_accessibility(
        self,
        image_data: bytes,
        content_type: str = 'image/png'
    ) -> str:
        """Generate accessibility-focused image description.
        
        Args:
            image_data: Raw image bytes
            content_type: MIME type
            
        Returns:
            Concise accessibility description
        """
        prompt = """Provide a concise accessibility description for this image suitable for alt-text. 
Keep it under 150 words, focus on the most important visual information."""
        
        result = self.analyze_image(image_data, content_type, prompt)
        
        if result.get('success'):
            return result.get('description', 'Image')
        return 'Image (description unavailable)'
    
    def _compress_if_needed(self, image_data: bytes, content_type: str) -> bytes:
        """Compress image if it exceeds size limits.
        
        Args:
            image_data: Original image bytes
            content_type: MIME type
            
        Returns:
            Potentially compressed image bytes
        """
        if len(image_data) <= MAX_IMAGE_SIZE_BYTES:
            return image_data
        
        if not HAS_PIL:
            logger.warning("Pillow not available for image compression")
            return image_data
        
        logger.info(f"Compressing image from {len(image_data)} bytes")
        
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Progressive quality reduction
            for quality in [85, 70, 50, 30]:
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                compressed = buffer.getvalue()
                
                if len(compressed) <= MAX_IMAGE_SIZE_BYTES:
                    logger.info(f"Compressed to {len(compressed)} bytes at quality {quality}")
                    return compressed
            
            # If still too large, resize
            ratio = (MAX_IMAGE_SIZE_BYTES / len(image_data)) ** 0.5
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=50, optimize=True)
            compressed = buffer.getvalue()
            
            logger.info(f"Resized and compressed to {len(compressed)} bytes")
            return compressed
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return image_data
    
    def analyze_images_batch(
        self,
        images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze multiple images.
        
        Args:
            images: List of dicts with 'data' (bytes) and 'content_type'
            
        Returns:
            List of analysis results
        """
        results = []
        for img in images:
            result = self.analyze_image(
                img.get('data', b''),
                img.get('content_type', 'image/png')
            )
            result['index'] = img.get('index', len(results))
            results.append(result)
        
        return results
