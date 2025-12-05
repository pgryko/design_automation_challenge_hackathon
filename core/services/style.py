"""
Style extraction and aggregation service.
"""

import json
import logging
from pathlib import Path

from django.conf import settings

from .gemini import GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


class StyleService:
    """
    Service for extracting and managing design styles.

    Handles:
    - Extracting style from individual assets
    - Aggregating styles across a project
    - Building style context for generation
    """

    def __init__(self, gemini_service: GeminiService | None = None):
        self.gemini = gemini_service or GeminiService()

    async def extract_asset_style(self, asset) -> dict:
        """
        Extract style information from a design asset.

        Args:
            asset: DesignAsset model instance

        Returns:
            Dictionary with extracted style information
        """
        from core.models import DesignAsset

        if not isinstance(asset, DesignAsset):
            raise ValueError("Expected DesignAsset instance")

        image_path = Path(settings.MEDIA_ROOT) / str(asset.image)

        if not image_path.exists():
            logger.error(f"Asset image not found: {image_path}")
            return {"error": "Image file not found"}

        try:
            style_data = await self.gemini.extract_style(image_path)

            # Update the asset with extracted style
            asset.extracted_style = style_data
            asset.extracted_description = style_data.get(
                "summary", json.dumps(style_data, indent=2)[:500]
            )
            await asset.asave()

            logger.info(f"Extracted style for asset {asset.pk}")
            return style_data

        except GeminiServiceError as e:
            logger.error(f"Failed to extract style for asset {asset.pk}: {e}")
            return {"error": str(e)}

    async def aggregate_project_style(self, project) -> str:
        """
        Aggregate style information from all project assets.

        Args:
            project: Project model instance

        Returns:
            Aggregated style summary string
        """
        from core.models import Project

        if not isinstance(project, Project):
            raise ValueError("Expected Project instance")

        # Get all assets with extracted styles
        assets = project.assets.exclude(extracted_style={})

        if not assets.exists():
            return ""

        # Collect all style data
        all_colors = []
        all_typography = []
        all_components = []
        all_visual_styles = []
        all_moods = []
        summaries = []

        async for asset in assets:
            style = asset.extracted_style

            if not style or "error" in style:
                continue

            # Collect colors
            if "colors" in style:
                colors = style["colors"]
                if isinstance(colors, dict):
                    for key, value in colors.items():
                        if key != "additional" and value:
                            all_colors.append(f"{key}: {value}")
                        elif key == "additional" and isinstance(value, list):
                            all_colors.extend(value)

            # Collect typography
            if "typography" in style:
                typo = style["typography"]
                if isinstance(typo, dict):
                    all_typography.append(typo.get("characteristics", ""))
                    all_typography.append(typo.get("heading_style", ""))

            # Collect component styles
            if "components" in style:
                comps = style["components"]
                if isinstance(comps, dict):
                    for key, value in comps.items():
                        if value:
                            all_components.append(f"{key}: {value}")

            # Collect visual style
            if "visual_style" in style:
                vs = style["visual_style"]
                if isinstance(vs, dict):
                    all_visual_styles.append(
                        f"Design: {vs.get('design_system', 'N/A')}, "
                        f"Borders: {vs.get('border_radius', 'N/A')}, "
                        f"Shadows: {vs.get('shadows', 'N/A')}"
                    )

            # Collect mood
            if "mood" in style:
                mood = style["mood"]
                if isinstance(mood, list):
                    all_moods.extend(mood)

            # Collect summaries
            if "summary" in style:
                summaries.append(style["summary"])

        # Build aggregated summary
        parts = []

        if all_colors:
            unique_colors = list(dict.fromkeys(all_colors))[:10]
            parts.append(f"**Colors**: {', '.join(unique_colors)}")

        if all_typography:
            unique_typo = list(dict.fromkeys([t for t in all_typography if t]))[:5]
            if unique_typo:
                parts.append(f"**Typography**: {'; '.join(unique_typo)}")

        if all_visual_styles:
            unique_vs = list(dict.fromkeys(all_visual_styles))[:3]
            parts.append(f"**Visual Style**: {'; '.join(unique_vs)}")

        if all_components:
            unique_comps = list(dict.fromkeys(all_components))[:8]
            parts.append(f"**Components**: {'; '.join(unique_comps)}")

        if all_moods:
            unique_moods = list(dict.fromkeys(all_moods))[:6]
            parts.append(f"**Mood**: {', '.join(unique_moods)}")

        if summaries:
            parts.append(f"**Summary**: {summaries[0]}")

        aggregated = "\n\n".join(parts)

        # Update project
        project.style_summary = aggregated
        await project.asave()

        logger.info(f"Aggregated style for project {project.pk}")
        return aggregated

    def build_style_context(self, project) -> str:
        """
        Build a style context string for generation prompts.

        Args:
            project: Project model instance

        Returns:
            Style context string for use in generation prompts
        """
        parts = []

        # Add aggregated style summary
        if project.style_summary:
            parts.append("## Overall Style Guide")
            parts.append(project.style_summary)

        # Add individual asset descriptions
        assets_with_style = project.assets.exclude(extracted_description="")
        if assets_with_style.exists():
            parts.append("\n## Asset-Specific Styles")
            for asset in assets_with_style[:5]:  # Limit to 5 most recent
                parts.append(
                    f"\n### {asset.filename} ({asset.get_asset_type_display()})"
                )
                parts.append(asset.extracted_description)

        # Add document context
        docs = project.documents.exclude(summary="")
        if docs.exists():
            parts.append("\n## Design Guidelines & Context")
            for doc in docs[:3]:  # Limit to 3
                parts.append(f"\n### {doc.title}")
                parts.append(doc.summary or doc.content[:500])

        return "\n".join(parts)

    async def analyze_all_assets(self, project) -> list[dict]:
        """
        Analyze all assets in a project that haven't been analyzed yet.

        Args:
            project: Project model instance

        Returns:
            List of extraction results
        """
        results = []

        # Get assets without extracted styles
        unanalyzed = project.assets.filter(extracted_style={})

        async for asset in unanalyzed:
            result = await self.extract_asset_style(asset)
            results.append({"asset_id": str(asset.pk), "result": result})

        # Update aggregated style
        if results:
            await self.aggregate_project_style(project)

        return results
