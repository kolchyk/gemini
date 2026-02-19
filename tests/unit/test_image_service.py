import unittest
import base64
from unittest.mock import MagicMock, patch
from services.image_service import ImageService

class TestImageService(unittest.TestCase):
    @patch('services.image_service.get_gemini_client')
    @patch('services.image_service.telegram_service')
    def test_generate_image_basic(self, mock_telegram_service, mock_get_gemini_client):
        # Setup mock client
        mock_client = MagicMock()
        mock_get_gemini_client.return_value = mock_client
        
        # Mock generate_content_stream response (it's a generator)
        mock_chunk = MagicMock()
        mock_chunk.candidates = [MagicMock()]
        mock_chunk.candidates[0].content.parts = [MagicMock()]
        
        # Use a real base64-encoded string for test stability
        mock_image_data_b64 = base64.b64encode(b"mock_image_bytes").decode('utf-8')
        mock_chunk.candidates[0].content.parts[0].inline_data.data = mock_image_data_b64
        mock_chunk.text = "Mock response text"
        
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        
        # Initialize service
        service = ImageService()
        
        # Test generate_image
        result = service.generate_image(prompt="test prompt")
        
        # Assertions
        self.assertIn('image_bytes', result)
        self.assertEqual(result['image_bytes'], b"mock_image_bytes")
        self.assertIn('text_output', result)
        self.assertEqual(result['text_output'], "Mock response text")
        
        # Verify calls
        mock_client.models.generate_content_stream.assert_called_once()
        mock_telegram_service.sync_send_image_log.assert_called_once()

    def test_generate_image_empty_prompt(self):
        service = ImageService() # Will trigger get_gemini_client in __init__ but we'll mock it if needed
        # Actually, let's mock get_gemini_client here as well or just let it fail if it's called
        with patch('services.image_service.get_gemini_client'):
            service = ImageService()
            with self.assertRaises(ValueError):
                service.generate_image(prompt="")

if __name__ == '__main__':
    unittest.main()
