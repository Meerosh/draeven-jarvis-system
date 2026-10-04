"""Offline/mocked tests for OpenAI image provider."""

import base64
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock openai module before importing provider
sys.modules["openai"] = MagicMock()

from providers.openai_provider import (
    OpenAIImageProvider,
    ImageGenerationRequest,
    ImageGenerationResult,
)


class TestOpenAIImageProvider(unittest.TestCase):
    """Offline tests for OpenAI provider using mocked API."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal PNG in memory for testing (1x1 transparent PNG)
        self.minimal_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    def test_provider_initializes_with_env_key(self):
        """Test that provider initializes with OPENAI_API_KEY from environment."""
        provider = OpenAIImageProvider()
        self.assertEqual(provider.api_key, "sk-test-key-12345")

    def test_provider_fails_without_api_key(self):
        """Test that provider raises if OPENAI_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True), patch(
            "providers.openai_provider._load_protected_openai_key", return_value=None
        ):
            with self.assertRaises(RuntimeError) as ctx:
                OpenAIImageProvider()
            self.assertIn("OpenAI API key is not configured", str(ctx.exception))

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    @patch("openai.OpenAI")
    def test_text_only_generation_request(self, mock_openai_class):
        """Test text-only image generation request (no reference image)."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock the API response
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].b64_json = base64.b64encode(self.minimal_png).decode()
        mock_client.images.generate.return_value = mock_response

        # Create provider and make request
        provider = OpenAIImageProvider()
        request = ImageGenerationRequest(
            model="gpt-image-2.5-sunburst",
            prompt="A magical O&L card design",
            size="1024x1536",
            quality="hd",
            n=1,
        )

        result = provider.generate(request)

        # Verify API was called correctly
        mock_client.images.generate.assert_called_once()
        call_kwargs = mock_client.images.generate.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "gpt-image-2.5-sunburst")
        self.assertEqual(call_kwargs["prompt"], "A magical O&L card design")
        self.assertEqual(call_kwargs["size"], "1024x1536")
        self.assertEqual(call_kwargs["quality"], "hd")
        self.assertEqual(call_kwargs["n"], 1)
        self.assertEqual(call_kwargs["response_format"], "b64_json")

        # Verify result
        self.assertIsInstance(result, ImageGenerationResult)
        self.assertEqual(result.image_bytes, self.minimal_png)
        self.assertEqual(result.model, "gpt-image-2.5-sunburst")
        self.assertFalse(result.reference_image_used)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    @patch("openai.OpenAI")
    def test_reference_image_generation_request(self, mock_openai_class):
        """Test image generation with reference image."""
        # Create a temporary reference image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(self.minimal_png)
            ref_image_path = Path(f.name)

        try:
            # Mock the OpenAI client
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock the API response
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].b64_json = base64.b64encode(self.minimal_png).decode()
            mock_client.images.edit.return_value = mock_response

            # Create provider and make request
            provider = OpenAIImageProvider()
            request = ImageGenerationRequest(
                model="gpt-image-2.5-sunburst",
                prompt="Enhance with Modern Arcane style",
                size="1024x1536",
                quality="hd",
                n=1,
                reference_image_path=ref_image_path,
            )

            result = provider.generate(request)

            # Verify API was called with edit endpoint
            mock_client.images.edit.assert_called_once()
            call_kwargs = mock_client.images.edit.call_args.kwargs
            self.assertEqual(call_kwargs["model"], "gpt-image-2.5-sunburst")
            self.assertEqual(call_kwargs["prompt"], "Enhance with Modern Arcane style")
            self.assertEqual(call_kwargs["size"], "1024x1536")
            self.assertEqual(call_kwargs["quality"], "hd")
            self.assertEqual(call_kwargs["n"], 1)
            self.assertEqual(call_kwargs["response_format"], "b64_json")

            # Verify result
            self.assertIsInstance(result, ImageGenerationResult)
            self.assertEqual(result.image_bytes, self.minimal_png)
            self.assertTrue(result.reference_image_used)

        finally:
            # Clean up temp file
            ref_image_path.unlink()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    def test_generation_fails_with_missing_reference_image(self):
        """Test that generation fails if reference image doesn't exist."""
        provider = OpenAIImageProvider()
        request = ImageGenerationRequest(
            model="gpt-image-2.5-sunburst",
            prompt="Test",
            size="1024x1536",
            quality="hd",
            reference_image_path=Path("/nonexistent/reference.png"),
        )

        with self.assertRaises(RuntimeError) as ctx:
            provider.generate(request)
        self.assertIn("Reference image not found", str(ctx.exception))

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    @patch("openai.OpenAI")
    def test_generation_fails_with_empty_response(self, mock_openai_class):
        """Test that generation fails if OpenAI returns empty response."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.images.generate.return_value = mock_response

        # Create provider and make request
        provider = OpenAIImageProvider()
        request = ImageGenerationRequest(
            model="gpt-image-2.5-sunburst",
            prompt="Test",
            size="1024x1536",
            quality="hd",
        )

        with self.assertRaises(RuntimeError) as ctx:
            provider.generate(request)
        self.assertIn("returned empty or invalid response", str(ctx.exception))

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
    def test_provider_requires_openai_package(self):
        """Test that provider gracefully fails if openai package is missing."""
        provider = OpenAIImageProvider()

        # Patch import to simulate missing openai package
        with patch("builtins.__import__", side_effect=ImportError("No module named 'openai'")):
            request = ImageGenerationRequest(
                model="gpt-image-2.5-sunburst",
                prompt="Test",
                size="1024x1536",
                quality="hd",
            )
            with self.assertRaises(RuntimeError) as ctx:
                provider.generate(request)
            self.assertIn("openai package not installed", str(ctx.exception))

    def test_image_generation_request_dataclass(self):
        """Test ImageGenerationRequest dataclass initialization."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(self.minimal_png)
            ref_path = Path(f.name)

        try:
            request = ImageGenerationRequest(
                model="gpt-image-2.5-sunburst",
                prompt="Test prompt",
                size="1024x1536",
                quality="hd",
                n=1,
                reference_image_path=ref_path,
            )
            self.assertEqual(request.model, "gpt-image-2.5-sunburst")
            self.assertEqual(request.prompt, "Test prompt")
            self.assertEqual(request.size, "1024x1536")
            self.assertEqual(request.quality, "hd")
            self.assertEqual(request.n, 1)
            self.assertEqual(request.reference_image_path, ref_path)
        finally:
            ref_path.unlink()

    def test_image_generation_result_dataclass(self):
        """Test ImageGenerationResult dataclass initialization."""
        result = ImageGenerationResult(
            image_bytes=self.minimal_png,
            model="gpt-image-2.5-sunburst",
            prompt="Test",
            size="1024x1536",
            quality="hd",
            reference_image_used=True,
        )
        self.assertEqual(result.image_bytes, self.minimal_png)
        self.assertEqual(result.model, "gpt-image-2.5-sunburst")
        self.assertTrue(result.reference_image_used)


if __name__ == "__main__":
    unittest.main()
