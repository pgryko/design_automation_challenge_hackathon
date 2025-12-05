"""
Gemini API service via OpenRouter.
"""

import base64
import json
import logging
from pathlib import Path

from django.conf import settings

import httpx

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Base exception for Gemini service errors."""

    pass


class GeminiService:
    """
    Service for interacting with Gemini via OpenRouter API.

    Handles:
    - Image analysis for style extraction
    - Image generation from prompts
    """

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.base_url = settings.OPENROUTER_BASE_URL

        if not self.api_key:
            raise GeminiServiceError("OPENROUTER_API_KEY is not configured")

    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/design-automation-challenge",
            "X-Title": "Design Automation Challenge",
        }

    def _encode_image(self, image_path: str | Path) -> str:
        """Encode an image file to base64."""
        path = Path(image_path)
        if not path.exists():
            raise GeminiServiceError(f"Image file not found: {path}")

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_mime_type(self, image_path: str | Path) -> str:
        """Get MIME type from file extension."""
        path = Path(image_path)
        suffix = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(suffix, "image/png")

    async def analyze_image(self, image_path: str | Path, prompt: str) -> str:
        """
        Analyze an image with a text prompt.

        Args:
            image_path: Path to the image file
            prompt: Analysis prompt/question

        Returns:
            Text response from the model
        """
        image_data = self._encode_image(image_path)
        mime_type = self._get_mime_type(image_path)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            if response.status_code != 200:
                logger.error(
                    f"Gemini API error: {response.status_code} - {response.text}"
                )
                raise GeminiServiceError(f"API error: {response.status_code}")

            data = response.json()
            result: str = data["choices"][0]["message"]["content"]
            return result

    async def extract_style(self, image_path: str | Path) -> dict:
        """
        Extract style information from a design image.

        Args:
            image_path: Path to the design image

        Returns:
            Dictionary with extracted style information
        """
        prompt = """Analyze this UI design image and extract detailed style information.

Return a JSON object with the following structure (respond ONLY with valid JSON, no markdown):
{
  "colors": {
    "primary": "#hex or description",
    "secondary": "#hex or description",
    "accent": "#hex or description",
    "background": "#hex or description",
    "text": "#hex or description",
    "additional": ["#hex", "..."]
  },
  "typography": {
    "heading_style": "description of heading fonts",
    "body_style": "description of body text",
    "font_weights": ["weights used"],
    "characteristics": "serif/sans-serif/monospace, etc."
  },
  "spacing": {
    "overall_feel": "tight/moderate/airy",
    "padding_pattern": "description",
    "layout_style": "description of layout approach"
  },
  "components": {
    "buttons": "description of button styles",
    "cards": "description of card styles if present",
    "inputs": "description of input field styles if present",
    "icons": "description of icon style if present"
  },
  "visual_style": {
    "design_system": "flat/material/neumorphic/glassmorphism/other",
    "border_radius": "none/subtle/moderate/rounded/pill",
    "shadows": "none/subtle/moderate/prominent",
    "borders": "none/subtle/prominent"
  },
  "mood": ["adjectives describing the design mood"],
  "summary": "2-3 sentence summary of the overall design language"
}"""

        response = await self.analyze_image(image_path, prompt)

        # Try to parse JSON from response
        try:
            # Handle case where response might have markdown code blocks
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            parsed: dict = json.loads(json_str.strip())
            return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse style JSON, returning raw response")
            return {
                "raw_response": response,
                "summary": response[:500] if len(response) > 500 else response,
            }

    async def generate_image(
        self,
        prompt: str,
        style_context: str = "",
        reference_images: list[str | Path] | None = None,
    ) -> bytes:
        """
        Generate a new design image based on prompt and style context.

        Args:
            prompt: Description of what to generate
            style_context: Style guide/description to follow
            reference_images: Optional list of reference image paths

        Returns:
            Generated image as bytes
        """
        # Build the message content
        content = []

        # Add reference images if provided
        if reference_images:
            for img_path in reference_images[:3]:  # Limit to 3 reference images
                image_data = self._encode_image(img_path)
                mime_type = self._get_mime_type(img_path)
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                    }
                )

        # Build the generation prompt
        full_prompt = f"""You are an expert UI/UX designer. Generate a new design image based on the following request.

STYLE GUIDE TO FOLLOW:
{style_context}

USER REQUEST:
{prompt}

IMPORTANT INSTRUCTIONS:
1. Generate a complete, production-ready UI design
2. Match the exact visual style described in the style guide
3. Use the same colors, typography, spacing, and component styles
4. Create realistic placeholder content where needed
5. The design should look like it belongs to the same product/brand

Generate the image now."""

        content.append({"type": "text", "text": full_prompt})

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 4096,
            "temperature": 0.8,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            if response.status_code != 200:
                logger.error(
                    f"Gemini API error: {response.status_code} - {response.text}"
                )
                raise GeminiServiceError(f"API error: {response.status_code}")

            data = response.json()

            # Check for image in response
            message = data["choices"][0]["message"]

            # Handle different response formats for image generation
            if "content" in message:
                content = message["content"]

                # If content is a list (multimodal response)
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "image_url":
                            image_url_data = item.get("image_url", {})
                            if isinstance(image_url_data, dict):
                                image_url = str(image_url_data.get("url", ""))
                                if image_url.startswith("data:"):
                                    # Extract base64 data
                                    base64_data = image_url.split(",")[1]
                                    return base64.b64decode(base64_data)

                # If content is a string, it might contain base64 image
                if isinstance(content, str):
                    if "data:image" in content:
                        base64_data = content.split(",")[1].split('"')[0]
                        return base64.b64decode(base64_data)

                    # Return as text if no image found (for debugging)
                    raise GeminiServiceError(
                        f"No image in response. Model returned: {content[:500]}"
                    )

            raise GeminiServiceError("Unexpected response format from API")

    async def generate_with_text_response(
        self,
        prompt: str,
        style_context: str = "",
        output_type: str = "ui_mockup",
    ) -> str:
        """
        Generate a design description/specification as text.

        Useful for flow diagrams or when image generation isn't available.

        Args:
            prompt: Description of what to generate
            style_context: Style guide/description to follow
            output_type: Type of output (ui_mockup, flow_diagram, etc.)

        Returns:
            Text description/specification
        """
        system_prompt = f"""You are an expert UI/UX designer. Create a detailed design specification.

STYLE GUIDE:
{style_context}

OUTPUT TYPE: {output_type}

Provide a detailed description that could be used to create the design, including:
- Layout structure
- Component placements
- Colors to use (from the style guide)
- Typography specifications
- Spacing and sizing
- Any specific UI elements needed"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            if response.status_code != 200:
                logger.error(
                    f"Gemini API error: {response.status_code} - {response.text}"
                )
                raise GeminiServiceError(f"API error: {response.status_code}")

            data = response.json()
            result: str = data["choices"][0]["message"]["content"]
            return result
