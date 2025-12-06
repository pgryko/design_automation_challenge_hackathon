#!/usr/bin/env python
"""
Generate demo outputs for the result/ folder.

Usage:
    uv run python scripts/generate_demo.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from core.services.gemini import GeminiService


async def generate_carveout_demos():
    """Generate demo outputs for the carveout folder."""
    service = GeminiService()
    output_dir = project_root / "result" / "carveout"
    output_dir.mkdir(parents=True, exist_ok=True)

    demos = [
        {
            "name": "landing_hero_v1.png",
            "prompt": """Design a modern SaaS landing page hero section with:
1. A bold headline: "Transform Your Workflow"
2. A subheadline explaining the product's key benefit
3. Two CTA buttons: "Start Free Trial" (primary) and "Watch Demo" (secondary)
4. A product screenshot or 3D illustration on the right side
5. Subtle gradient background (purple to blue)
6. Clean, professional tech startup aesthetic
7. Floating UI elements for visual interest""",
            "style": """Modern tech startup design:
- Colors: Purple (#6366F1) primary, Blue (#3B82F6) secondary, Dark text on light background
- Typography: Bold sans-serif headings, regular body text
- Spacing: Generous whitespace, clear visual hierarchy
- Components: Rounded buttons, soft shadows, subtle gradients
- Visual style: Clean, professional, trustworthy, innovative""",
        },
        {
            "name": "mobile_fitness_v1.png",
            "prompt": """Design a mobile fitness app home screen (iPhone format) showing:
1. Top status bar with time and icons
2. Greeting header "Good Morning, Alex" with profile avatar
3. Today's workout card with exercise details and "Start" button
4. Weekly progress ring showing 4/7 days completed
5. Quick action buttons: Log Meal, Track Water, Check Stats
6. Bottom navigation bar with 5 icons (Home, Workouts, Nutrition, Progress, Profile)
7. iOS-style design with SF Pro font""",
            "style": """iOS fitness app design:
- Colors: Vibrant green (#22C55E) accent, Dark (#1F2937) and light backgrounds
- Typography: SF Pro style, medium weight headings, regular body
- Spacing: Compact but readable, iOS standard margins
- Components: iOS-style cards with rounded corners (16px), subtle shadows
- Visual style: Energetic, motivating, clean iOS aesthetic""",
        },
        {
            "name": "pricing_table_v1.png",
            "prompt": """Design a SaaS pricing page section showing 3 pricing tiers:
1. Basic tier ($9/mo): 5 projects, 10GB storage, Email support
2. Pro tier ($29/mo, highlighted as "Most Popular"): Unlimited projects, 100GB, Priority support, API access
3. Enterprise tier (Custom): Everything in Pro, SSO, Dedicated manager, Custom integrations
4. Each card has: Tier name, price, feature list with checkmarks, CTA button
5. Toggle switch for Monthly/Annual billing at the top
6. Clean, trustworthy design that encourages the Pro tier""",
            "style": """B2B SaaS pricing design:
- Colors: Blue (#2563EB) primary, Green for highlights, Gray (#6B7280) secondary text
- Typography: Clean sans-serif, bold pricing numbers, regular feature text
- Spacing: Well-organized cards with consistent padding
- Components: Rounded cards, checkmark icons, prominent CTAs
- Visual style: Professional, trustworthy, clear value proposition""",
        },
    ]

    for demo in demos:
        print(f"Generating {demo['name']}...")
        try:
            image_bytes = await service.generate_image(
                prompt=demo["prompt"],
                style_context=demo["style"],
            )
            output_path = output_dir / demo["name"]
            output_path.write_bytes(image_bytes)
            print(f"  Saved: {output_path} ({len(image_bytes) / 1024:.1f} KB)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone! Generated outputs in result/carveout/")


if __name__ == "__main__":
    asyncio.run(generate_carveout_demos())
