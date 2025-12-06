"""
Tests for core services (GeminiService, DocumentService).
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile

import pytest

from core.services.document import (
    DOCLING_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    TEXT_EXTENSIONS,
    extract_content,
    get_supported_extensions,
)
from core.services.gemini import GeminiService, GeminiServiceError


class TestDocumentService:
    """Tests for the document extraction service."""

    def test_supported_extensions_includes_common_formats(self):
        """Test that common document formats are supported."""
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".md" in SUPPORTED_EXTENSIONS

    def test_text_extensions_defined(self):
        """Test that text extensions are defined."""
        assert ".txt" in TEXT_EXTENSIONS
        assert ".md" in TEXT_EXTENSIONS

    def test_docling_extensions_defined(self):
        """Test that Docling-processed extensions are defined."""
        assert ".pdf" in DOCLING_EXTENSIONS
        assert ".docx" in DOCLING_EXTENSIONS
        assert ".pptx" in DOCLING_EXTENSIONS

    def test_get_supported_extensions_returns_sorted_list(self):
        """Test that get_supported_extensions returns a sorted list."""
        extensions = get_supported_extensions()
        assert isinstance(extensions, list)
        assert extensions == sorted(extensions)
        assert ".pdf" in extensions

    def test_extract_content_txt_file(self):
        """Test extracting content from a plain text file."""
        content = "Hello, this is a test document.\nWith multiple lines."
        file = SimpleUploadedFile(
            name="test.txt",
            content=content.encode("utf-8"),
            content_type="text/plain",
        )
        result = extract_content(file)
        assert result == content

    def test_extract_content_md_file(self):
        """Test extracting content from a markdown file."""
        content = "# Heading\n\nSome **bold** text."
        file = SimpleUploadedFile(
            name="readme.md",
            content=content.encode("utf-8"),
            content_type="text/markdown",
        )
        result = extract_content(file)
        assert result == content

    def test_extract_content_unsupported_file_raises_error(self):
        """Test that unsupported file types raise ValueError."""
        file = SimpleUploadedFile(
            name="test.xyz",
            content=b"some content",
            content_type="application/octet-stream",
        )
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_content(file)

    def test_extract_content_empty_txt_file(self):
        """Test extracting content from an empty text file."""
        file = SimpleUploadedFile(
            name="empty.txt",
            content=b"",
            content_type="text/plain",
        )
        result = extract_content(file)
        assert result == ""  # Empty files return empty string

    @patch("core.services.document._extract_with_docling")
    def test_extract_content_pdf_uses_docling(self, mock_docling):
        """Test that PDF files use Docling for extraction."""
        mock_docling.return_value = "Extracted PDF content"
        file = SimpleUploadedFile(
            name="document.pdf",
            content=b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
        )
        result = extract_content(file)
        assert result == "Extracted PDF content"
        mock_docling.assert_called_once()


class TestGeminiService:
    """Tests for the Gemini AI service."""

    def test_init_with_defaults(self):
        """Test GeminiService initializes with defaults from settings."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "test-model"
            mock_settings.OPENROUTER_BASE_URL = "https://test.api"

            service = GeminiService()

            assert service.api_key == "test-key"
            assert service.model == "test-model"
            assert service.base_url == "https://test.api"

    def test_get_headers_includes_auth(self):
        """Test that headers include authorization."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-api-key"
            mock_settings.OPENROUTER_MODEL = "test-model"
            mock_settings.OPENROUTER_BASE_URL = "https://test.api"

            service = GeminiService()
            headers = service._get_headers()

            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-api-key"
            assert headers["Content-Type"] == "application/json"

    def test_get_mime_type_png(self):
        """Test MIME type detection for PNG."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.OPENROUTER_MODEL = "model"
            mock_settings.OPENROUTER_BASE_URL = "url"

            service = GeminiService()
            assert service._get_mime_type("image.png") == "image/png"
            assert service._get_mime_type(Path("image.png")) == "image/png"

    def test_get_mime_type_jpg(self):
        """Test MIME type detection for JPEG."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.OPENROUTER_MODEL = "model"
            mock_settings.OPENROUTER_BASE_URL = "url"

            service = GeminiService()
            assert service._get_mime_type("photo.jpg") == "image/jpeg"
            assert service._get_mime_type("photo.jpeg") == "image/jpeg"

    def test_get_mime_type_gif(self):
        """Test MIME type detection for GIF."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.OPENROUTER_MODEL = "model"
            mock_settings.OPENROUTER_BASE_URL = "url"

            service = GeminiService()
            assert service._get_mime_type("animation.gif") == "image/gif"

    def test_get_mime_type_default(self):
        """Test MIME type defaults to PNG for unknown extensions."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.OPENROUTER_MODEL = "model"
            mock_settings.OPENROUTER_BASE_URL = "url"

            service = GeminiService()
            assert service._get_mime_type("file.unknown") == "image/png"


@pytest.mark.asyncio
class TestGeminiServiceAsync:
    """Async tests for the Gemini AI service."""

    @pytest.fixture
    def mock_service(self):
        """Create a GeminiService with mocked settings."""
        with patch("core.services.gemini.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = "test-key"
            mock_settings.OPENROUTER_MODEL = "test-model"
            mock_settings.OPENROUTER_BASE_URL = "https://test.api"
            yield GeminiService()

    async def test_generate_image_success(self, mock_service):
        """Test successful image generation."""
        import base64

        # Create a fake image response
        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Minimal PNG header
        base64_image = base64.b64encode(fake_image).decode()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "images": [
                            {"image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await mock_service.generate_image(
                prompt="Test prompt",
                style_context="Test style",
            )

            assert result == fake_image

    async def test_generate_image_api_error(self, mock_service):
        """Test that API errors raise GeminiServiceError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(GeminiServiceError, match="API error: 500"):
                await mock_service.generate_image(
                    prompt="Test prompt",
                    style_context="Test style",
                )

    async def test_extract_style_success(self, mock_service):
        """Test successful style extraction."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"colors": {"primary": "#007bff"}, "summary": "Modern blue theme"}'
                    }
                }
            ]
        }

        # Create a temporary image file
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Mock file reading
            with patch.object(mock_service, "_encode_image", return_value="base64data"):
                result = await mock_service.extract_style(Path("test.png"))

                assert "colors" in result
                assert result["colors"]["primary"] == "#007bff"

    async def test_refine_image_success(self, mock_service):
        """Test successful image refinement."""
        import base64

        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        base64_image = base64.b64encode(fake_image).decode()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "images": [
                            {"image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with patch.object(mock_service, "_encode_image", return_value="base64data"):
                result = await mock_service.refine_image(
                    original_image_path=Path("original.png"),
                    refinement_prompt="Make it darker",
                    style_context="Dark theme",
                )

                assert result == fake_image
