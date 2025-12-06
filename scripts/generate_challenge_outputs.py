#!/usr/bin/env python
"""
Generate example prompt outputs for hackathon submission.

Generates outputs matching the DQAI and Carveout example prompts
from the Design Automation Challenge PDF.

Usage:
    uv run python scripts/generate_challenge_outputs.py
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

# OCC/JiVS Enterprise Style Context
OCC_STYLE = """Enterprise SaaS application design (JiVS/OCC product suite):
- Colors: Primary blue (#1E40AF), Secondary gray (#374151), Success green (#059669),
  Warning amber (#D97706), Error red (#DC2626), Background light gray (#F3F4F6)
- Typography: Inter or system sans-serif, semibold headings, regular body text
- Spacing: Generous padding (24px cards), clear visual hierarchy, data-dense but readable
- Components: Clean data tables with alternating rows, status badges, progress indicators,
  sidebar navigation, breadcrumbs, action buttons (primary blue, secondary outline)
- Visual style: Professional enterprise software, trustworthy, data-focused, German engineering quality
- Charts: Line charts for trends, clean axes, blue/green color scheme
- Tables: Sortable headers, status columns with colored badges, action buttons per row
"""


async def generate_dqai_outputs():
    """Generate DQAI (Data Quality AI) example outputs."""
    service = GeminiService()
    output_dir = project_root / "result" / "dqai"
    output_dir.mkdir(parents=True, exist_ok=True)

    screens = [
        {
            "name": "01_project_systems.png",
            "prompt": """Design an enterprise dashboard screen for OCC (Operations Control Center) showing:

1. Left sidebar with navigation: Dashboard, Projects, Systems, Transfers, Analysis, Settings
2. Header with "OCC" logo, breadcrumb "Projects > SAP Migration Project", user profile
3. Main content: "Associated Systems" section showing 3 SAP system cards:
   - SAP ERP (Production) - Status: Connected (green badge)
   - SAP BW (Analytics) - Status: Connected (green badge)
   - SAP CRM (Legacy) - Status: Pending (amber badge)
4. Each card shows: System name, type, connection status, last sync time, "Configure" button
5. "Add System" button in top right of the section
6. Summary stats bar: "3 Systems | 2 Connected | 1 Pending"

Enterprise SaaS style with professional blue/gray palette, clean data presentation.""",
            "style": OCC_STYLE,
        },
        {
            "name": "02_installation_progress.png",
            "prompt": """Design an enterprise installation progress screen for JiVS IMP setup showing:

1. Left sidebar with navigation (same as before)
2. Header with breadcrumb "Projects > SAP Migration > Installation"
3. Main content showing installation wizard with progress stepper:
   - Step 1: Provision Azure Environment ✓ (completed, green)
   - Step 2: Install JiVS IMP ✓ (completed, green)
   - Step 3: Configure Mediator (current, blue, spinning)
   - Step 4: Prepare Export Handler (pending, gray)
   - Step 5: Validate Connection (pending, gray)
4. Current step details panel:
   - "Configuring Mediator App..." with progress bar at 65%
   - Log output showing recent activities
   - Estimated time remaining: "~3 minutes"
5. Cancel and "View Logs" buttons at bottom

Professional enterprise installer UI with clear progress indication.""",
            "style": OCC_STYLE,
        },
        {
            "name": "03_data_transfer.png",
            "prompt": """Design an enterprise data transfer monitoring screen showing:

1. Left sidebar navigation with "Transfers" highlighted
2. Header with breadcrumb "Projects > SAP Migration > Data Transfer"
3. Summary cards row: "Total Tables: 47", "Completed: 32", "In Progress: 8", "Pending: 7"
4. Main data table with columns:
   - Table Name (e.g., MARA, MARC, VBAK, VBAP, KNA1)
   - Records count
   - Status badge (Success=green, In Progress=blue spinner, Pending=gray)
   - Started timestamp
   - Completed timestamp
   - Actions (View, Retry)
5. Show mix of statuses: some Success, some In Progress with progress %, some Pending
6. Pagination showing "Page 1 of 3"
7. Filter/search bar above table
8. Overall progress bar at top showing "68% Complete"

Enterprise data pipeline monitoring interface.""",
            "style": OCC_STYLE,
        },
        {
            "name": "04_analysis_results.png",
            "prompt": """Design an enterprise analytics dashboard for Data Quality AI results showing:

1. Left sidebar with "Analysis" highlighted
2. Header with breadcrumb "Projects > SAP Migration > Analysis Results"
3. Top summary cards in a row:
   - Data Quality Score: 94.2% (large green number with trend arrow up)
   - Total Records Analyzed: 2,847,392
   - Issues Found: 1,247
   - Tables Scanned: 47
4. Main chart area: Line chart showing "Data Quality Score Over Time"
   - X-axis: dates (Nov 15 - Dec 5)
   - Y-axis: Quality Score (85-100%)
   - Blue line trending upward with data points
5. Below chart: "Issue Breakdown by Category" bar chart
   - Missing Values: 423
   - Format Errors: 312
   - Referential Integrity: 287
   - Duplicates: 225
6. "Run New Analysis" button and "Export Report" button

Professional analytics dashboard with clear data visualization.""",
            "style": OCC_STYLE,
        },
        {
            "name": "05_run_history.png",
            "prompt": """Design an enterprise run history screen for analysis operations showing:

1. Left sidebar with "Analysis" highlighted, sub-item "History" selected
2. Header with breadcrumb "Projects > SAP Migration > Analysis > Run History"
3. Filter bar: Date range picker, Status dropdown, "Apply Filters" button
4. Main table showing past analysis runs:
   | Run ID | Started | Duration | Status | Records | Score | Actions |
   | #127   | Dec 5, 14:32 | 8m 42s | Success | 2.8M | 94.2% | View |
   | #126   | Dec 4, 09:15 | 7m 58s | Success | 2.8M | 93.8% | View |
   | #125   | Dec 3, 11:20 | 9m 12s | Success | 2.7M | 92.1% | View |
   | #124   | Dec 2, 16:45 | 2m 33s | Failed  | 1.2M | -     | View |
   | #123   | Dec 1, 10:00 | 8m 15s | Success | 2.7M | 91.5% | View |
5. Status badges: Success (green), Failed (red), Running (blue)
6. Pagination: "Showing 1-5 of 23 runs"
7. "Schedule Analysis" and "Run Now" buttons in top right

Enterprise audit/history table with sortable columns.""",
            "style": OCC_STYLE,
        },
    ]

    for screen in screens:
        print(f"Generating DQAI: {screen['name']}...")
        try:
            image_bytes = await service.generate_image(
                prompt=screen["prompt"],
                style_context=screen["style"],
            )
            output_path = output_dir / screen["name"]
            output_path.write_bytes(image_bytes)
            print(f"  ✓ Saved: {output_path.name} ({len(image_bytes) / 1024:.1f} KB)")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    print("\n✓ DQAI outputs complete!")


async def generate_carveout_outputs():
    """Generate Carveout example outputs."""
    service = GeminiService()
    output_dir = project_root / "result" / "carveout"

    # Clear old demo files
    if output_dir.exists():
        for old_file in output_dir.glob("*.png"):
            old_file.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    screens = [
        {
            "name": "01_project_systems.png",
            "prompt": """Design an enterprise dashboard screen for OCC Carveout project showing:

1. Left sidebar: Dashboard, Projects, Systems, Transfers, Carveout, Settings
2. Header with "OCC" logo, breadcrumb "Projects > Carveout Project Q4", user profile
3. Main content: "Source Systems" section showing SAP systems:
   - SAP ERP (Production) - Status: Connected, 12.4M records
   - SAP HR (Personnel) - Status: Connected, 847K records
4. Target section: "Carveout Target" card showing Azure destination
5. Project timeline: "Phase: Data Transfer | Target: Dec 15"
6. Quick stats: "2 Source Systems | 13.2M Records | Carveout Scope: TBD"

Enterprise project overview for data carveout operation.""",
            "style": OCC_STYLE,
        },
        {
            "name": "02_data_transfer.png",
            "prompt": """Design an enterprise data transfer screen for Carveout showing:

1. Left sidebar with "Transfers" highlighted
2. Header: "Projects > Carveout Project > Data Transfer"
3. Progress banner: "Transfer Progress: 87% Complete" with progress bar
4. Transfer table with columns:
   - Source Table | Records | Transferred | Status | ETA
   - PA0001 (Personnel) | 234,521 | 234,521 | ✓ Success | -
   - PA0002 (Personal Data) | 189,432 | 189,432 | ✓ Success | -
   - HRP1000 (Objects) | 892,341 | 756,890 | ⟳ In Progress | 4 min
   - HRP1001 (Relationships) | 1,245,678 | - | ○ Pending | 12 min
5. Status indicators with colored badges
6. "Pause Transfer" and "View Logs" buttons

Data pipeline transfer monitoring for carveout.""",
            "style": OCC_STYLE,
        },
        {
            "name": "03_carveout_definition.png",
            "prompt": """Design a Carveout definition/configuration screen showing:

1. Left sidebar with "Carveout" highlighted
2. Header: "Projects > Carveout Project > Define Carveout"
3. Carveout criteria form:
   - "Organizational Units" multi-select dropdown (Company Code: 1000, 2000, 3000)
   - "Time Slice" date range picker (From: Jan 1, 2020 | To: Dec 31, 2024)
   - "Personnel Area" checkboxes (selected: DE01, DE02, US01)
   - "Include Inactive Records" toggle (Off)
4. Scope preview panel on right:
   - "Estimated Records: 3,247,891"
   - "Affected Tables: 24"
   - "Data Size: ~12.4 GB"
5. "Validate Scope" and "Save Definition" buttons
6. Warning banner: "Validation recommended before carveout execution"

Enterprise carveout scoping interface with filter configuration.""",
            "style": OCC_STYLE,
        },
        {
            "name": "04_subset_validation.png",
            "prompt": """Design a Carveout subset validation/preview screen showing:

1. Left sidebar with "Carveout" > "Validation" highlighted
2. Header: "Projects > Carveout Project > Subset Validation"
3. Validation status banner: "Validation Complete - 2 Warnings" (amber)
4. Summary cards:
   - Total Records: 3,247,891 ✓
   - Tables Affected: 24 ✓
   - Referential Integrity: Passed ✓
   - Orphan Records: 127 ⚠
5. Affected entities breakdown table:
   | Entity Type | Records | Status |
   | Employees | 12,453 | ✓ Valid |
   | Cost Centers | 234 | ✓ Valid |
   | Org Units | 89 | ⚠ 3 orphaned |
   | Positions | 1,247 | ✓ Valid |
6. "View Orphan Details" link for warnings
7. "Proceed to Carveout" button (enabled) and "Redefine Scope" button
8. Readiness indicator: "Ready for Carveout Execution"

Subset validation and data integrity checking interface.""",
            "style": OCC_STYLE,
        },
        {
            "name": "05_carveout_results.png",
            "prompt": """Design a Carveout results dashboard with trend chart showing:

1. Left sidebar with "Carveout" > "Results" highlighted
2. Header: "Projects > Carveout Project > Carveout Results"
3. Latest run summary cards:
   - Records Carved: 3,247,891
   - Tables Processed: 24
   - Duration: 47m 23s
   - Status: Success ✓
4. Main chart: "Carved Data Volume Over Time" line chart
   - X-axis: Run dates (Run #1 through Run #5)
   - Y-axis: Records (millions, 0-4M)
   - Blue line showing carved records per run
   - Data points with values labeled
5. Destination status: "Target System: Ready | Last Sync: 5 min ago"
6. "Forward to Target" button and "Download Manifest" button

Carveout execution results with trend visualization.""",
            "style": OCC_STYLE,
        },
        {
            "name": "06_run_history.png",
            "prompt": """Design a Carveout run history screen showing:

1. Left sidebar with "Carveout" > "History" highlighted
2. Header: "Projects > Carveout Project > Carveout History"
3. Filter bar: Date range, Status filter, Scope filter
4. History table:
   | Run # | Date | Scope | Records | Duration | Status | Target |
   | #5 | Dec 5, 2024 | Full | 3.24M | 47m | Success | Forwarded |
   | #4 | Dec 3, 2024 | Partial | 1.12M | 18m | Success | Forwarded |
   | #3 | Nov 28, 2024 | Full | 3.19M | 52m | Success | Pending |
   | #2 | Nov 20, 2024 | Test | 50K | 2m | Success | N/A |
   | #1 | Nov 15, 2024 | Test | 25K | 1m | Failed | N/A |
5. Status badges colored appropriately
6. Actions column with "View Details" and "Re-run" options
7. "Export History" and "New Carveout Run" buttons

Carveout operation audit trail and history.""",
            "style": OCC_STYLE,
        },
    ]

    for screen in screens:
        print(f"Generating Carveout: {screen['name']}...")
        try:
            image_bytes = await service.generate_image(
                prompt=screen["prompt"],
                style_context=screen["style"],
            )
            output_path = output_dir / screen["name"]
            output_path.write_bytes(image_bytes)
            print(f"  ✓ Saved: {output_path.name} ({len(image_bytes) / 1024:.1f} KB)")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

    print("\n✓ Carveout outputs complete!")


async def main():
    """Generate all challenge outputs."""
    print("=" * 60)
    print("Design Automation Challenge - Output Generation")
    print("=" * 60)
    print()

    print("Generating DQAI (Data Quality AI) screens...")
    print("-" * 40)
    await generate_dqai_outputs()

    print()
    print("Generating Carveout screens...")
    print("-" * 40)
    await generate_carveout_outputs()

    print()
    print("=" * 60)
    print("All outputs generated in result/ folder")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
