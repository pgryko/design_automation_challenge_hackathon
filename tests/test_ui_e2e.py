"""
End-to-end UI tests using Playwright.

These tests verify the main user flows and UI components work correctly.
Run with: pytest tests/test_ui_e2e.py -v --headed (for visible browser)
"""

import re
from pathlib import Path

import pytest
from django.test import LiveServerTestCase
from playwright.sync_api import Page, expect

from core.models import Project


@pytest.fixture
def test_image(tmp_path: Path) -> Path:
    """Create a simple test image for upload tests."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="blue")
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return img_path


@pytest.fixture
def project_with_style(db) -> Project:
    """Create a project with extracted style for testing."""
    return Project.objects.create(
        name="Test Project with Style",
        description="A project with style summary for testing",
        style_summary="""**Colors**: primary: #1a417f (Deep blue), secondary: #ffffff (White), accent: #28a745 (Green)

**Typography**: Sans-serif font family

**Visual Style**: Modern, clean design
""",
    )


class TestProjectList:
    """Tests for the project list page."""

    @pytest.mark.django_db(transaction=True)
    def test_empty_state_shows_welcome_message(
        self, page: Page, live_server
    ) -> None:
        """Empty project list shows welcome message and how-it-works guide."""
        page.goto(live_server.url)

        # Check welcome message
        expect(page.get_by_text("Welcome to Design Automation")).to_be_visible()

        # Check how-it-works steps
        expect(page.get_by_text("Upload Assets")).to_be_visible()
        expect(page.get_by_text("AI Analyzes Style")).to_be_visible()
        expect(page.get_by_text("Generate Designs")).to_be_visible()

        # Check create button
        expect(
            page.get_by_role("button", name="Create Your First Project")
        ).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_project_cards_display(self, page: Page, live_server, project) -> None:
        """Projects are displayed as cards with correct information."""
        page.goto(live_server.url)

        # Project card should be visible - use heading for specificity
        expect(page.get_by_role("heading", name=project.name)).to_be_visible()

        # Asset and generation counts should show
        expect(page.get_by_text("0 assets")).to_be_visible()
        expect(page.get_by_text("0 generations")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_new_project_button(self, page: Page, live_server) -> None:
        """New Project button opens create modal."""
        page.goto(live_server.url)

        # Click new project button (use first matching button)
        page.get_by_role("button", name="New Project").first.click()

        # Wait for modal to load via HTMX
        page.wait_for_selector("#modal-container form")

        # Modal should appear with form
        expect(page.get_by_label("Name")).to_be_visible()
        expect(page.get_by_label("Description")).to_be_visible()


class TestProjectCreate:
    """Tests for project creation."""

    @pytest.mark.django_db(transaction=True)
    def test_create_project_via_modal(self, page: Page, live_server) -> None:
        """Creating a project via modal adds it to the list."""
        page.goto(live_server.url)

        # Open create modal (use first matching button)
        page.get_by_role("button", name=re.compile("New Project|Create Your First")).first.click()

        # Wait for modal to load
        page.wait_for_selector("#modal-container form")

        # Fill form
        page.get_by_label("Name").fill("My New Project")
        page.get_by_label("Description").fill("A test project description")

        # Submit
        page.locator("#modal-container").get_by_role("button", name="Create Project").click()

        # Wait for the project heading to appear (either redirect or success)
        expect(page.get_by_role("heading", name="My New Project")).to_be_visible(
            timeout=10000
        )


class TestProjectDetail:
    """Tests for project detail page."""

    @pytest.mark.django_db(transaction=True)
    def test_tab_navigation(self, page: Page, live_server, project) -> None:
        """Tabs navigate between different sections."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        # All tabs should be visible
        expect(page.get_by_role("button", name=re.compile("Assets"))).to_be_visible()
        expect(page.get_by_role("button", name=re.compile("Documents"))).to_be_visible()
        expect(page.get_by_role("button", name="Generate")).to_be_visible()
        expect(page.get_by_role("button", name=re.compile("History"))).to_be_visible()

        # Click Documents tab
        page.get_by_role("button", name=re.compile("Documents")).click()

        # Documents content should be visible - look for upload text
        expect(page.get_by_text("Upload File")).to_be_visible()

        # Click Generate tab
        page.get_by_role("button", name="Generate").click()

        # Generate content should be visible
        expect(page.get_by_text("Generate New Designs")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_tab_counters_display(self, page: Page, live_server, project) -> None:
        """Tab counters show correct counts."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        # Counters should show 0 for empty project
        expect(page.get_by_role("button", name="Assets 0")).to_be_visible()
        expect(page.get_by_role("button", name="Documents 0")).to_be_visible()
        expect(page.get_by_role("button", name="History 0")).to_be_visible()


class TestAssetsTab:
    """Tests for the Assets tab functionality."""

    @pytest.mark.django_db(transaction=True)
    def test_upload_zone_visible(self, page: Page, live_server, project) -> None:
        """Upload zone is displayed on Assets tab."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        expect(page.get_by_text("Upload design assets")).to_be_visible()
        expect(page.get_by_text("or drag and drop")).to_be_visible()
        expect(page.get_by_text("PNG, JPG, GIF up to 10MB")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_asset_type_dropdown(self, page: Page, live_server, project) -> None:
        """Asset type dropdown has all options."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        dropdown = page.locator("select").first
        expect(dropdown).to_be_visible()

        # Check options
        options = dropdown.locator("option").all_text_contents()
        assert "UI Screenshot" in options
        assert "Style Guide" in options
        assert "Brand Image" in options

    @pytest.mark.django_db(transaction=True)
    def test_color_swatches_display(
        self, page: Page, live_server, project_with_style
    ) -> None:
        """Color swatches render from style summary."""
        page.goto(f"{live_server.url}/projects/{project_with_style.pk}/")

        # Color swatches container should exist
        swatches = page.locator('[style*="display: flex"][style*="flex-wrap: wrap"]')
        expect(swatches).to_be_visible()

        # Individual swatches should be visible
        swatch_elements = swatches.locator("div > div").all()
        assert len(swatch_elements) >= 3  # At least 3 colors in our test data

    @pytest.mark.django_db(transaction=True)
    def test_style_analysis_collapsible(
        self, page: Page, live_server, project_with_style
    ) -> None:
        """Style analysis is in a collapsible details element."""
        page.goto(f"{live_server.url}/projects/{project_with_style.pk}/")

        # Collapsible summary should be visible
        summary = page.get_by_text("View full style analysis")
        expect(summary).to_be_visible()

        # Click to expand
        summary.click()

        # Full style text should now be visible
        expect(page.get_by_text("Typography")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_no_style_message(self, page: Page, live_server, project) -> None:
        """Projects without style show appropriate message."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        expect(page.get_by_text("No style extracted yet")).to_be_visible()


class TestGenerateTab:
    """Tests for the Generate tab functionality."""

    @pytest.mark.django_db(transaction=True)
    def test_generate_form_visible(self, page: Page, live_server, project) -> None:
        """Generate form displays with all fields."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        expect(page.get_by_text("Generate New Designs")).to_be_visible()
        expect(
            page.get_by_placeholder(re.compile("Generate a 3-screen"))
        ).to_be_visible()
        expect(page.get_by_label("Output Type")).to_be_visible()
        expect(page.get_by_label("Number of Variations")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_form_validation_empty(self, page: Page, live_server, project) -> None:
        """Empty prompt shows validation message and disables button."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        # Initial state - button disabled (the submit button inside the form)
        generate_btn = page.locator("#generation-form button[type='submit']")
        expect(generate_btn).to_be_disabled()

        # Validation message - use exact match to avoid header text
        expect(
            page.get_by_text("Describe what you want to create", exact=True)
        ).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_form_validation_short_prompt(
        self, page: Page, live_server, project
    ) -> None:
        """Short prompt shows 'keep going' message."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        # Type short text
        page.get_by_placeholder(re.compile("Generate a 3-screen")).fill("Test")

        # Validation message changes
        expect(page.get_by_text("Keep going")).to_be_visible()

        # Button still disabled
        generate_btn = page.locator("#generation-form button[type='submit']")
        expect(generate_btn).to_be_disabled()

    @pytest.mark.django_db(transaction=True)
    def test_form_validation_valid_prompt(
        self, page: Page, live_server, project
    ) -> None:
        """Valid prompt shows 'ready' message and enables button."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        # Type valid text (10+ chars)
        page.get_by_placeholder(re.compile("Generate a 3-screen")).fill(
            "Create a dashboard for analytics"
        )

        # Validation message changes
        expect(page.get_by_text("Ready to generate!")).to_be_visible()

        # Button enabled
        generate_btn = page.locator("#generation-form button[type='submit']")
        expect(generate_btn).to_be_enabled()

    @pytest.mark.django_db(transaction=True)
    def test_context_preview_no_assets(
        self, page: Page, live_server, project
    ) -> None:
        """Context preview shows warning when no assets."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        # Look for the specific warning text
        expect(page.get_by_text("No assets (style may be generic)")).to_be_visible()

    @pytest.mark.django_db(transaction=True)
    def test_output_type_options(self, page: Page, live_server, project) -> None:
        """Output type dropdown has correct options."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name="Generate").click()

        dropdown = page.get_by_label("Output Type")
        options = dropdown.locator("option").all_text_contents()

        assert "UI Mockup" in options
        assert "Flow Diagram" in options
        assert "Marketing Banner" in options


class TestDocumentsTab:
    """Tests for the Documents tab functionality."""

    @pytest.mark.django_db(transaction=True)
    def test_upload_zone_visible(self, page: Page, live_server, project) -> None:
        """Document upload zone is visible."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")
        page.get_by_role("button", name=re.compile("Documents")).click()

        expect(page.get_by_text("Upload File")).to_be_visible()


class TestProjectActions:
    """Tests for project edit and delete actions."""

    @pytest.mark.django_db(transaction=True)
    def test_edit_button_opens_modal(self, page: Page, live_server, project) -> None:
        """Edit button opens edit modal."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        page.get_by_role("button", name="Edit").click()

        expect(page.get_by_role("heading", name="Edit Project")).to_be_visible()
        expect(page.get_by_label("Name")).to_have_value(project.name)

    @pytest.mark.django_db(transaction=True)
    def test_delete_button_shows_confirmation(
        self, page: Page, live_server, project
    ) -> None:
        """Delete button shows styled confirmation modal."""
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        # Click delete button - opens confirmation modal
        page.get_by_role("button", name="Delete").click()

        # Wait for modal content to load (HTMX injects it)
        page.wait_for_function(
            "document.querySelector('#modal-container')?.textContent?.includes('Delete Project')",
            timeout=5000,
        )

        # Give Alpine.js time to initialize and show the modal
        page.wait_for_timeout(300)

        # Confirmation modal should appear with project name and warning
        expect(page.get_by_role("heading", name="Delete Project")).to_be_visible()
        expect(page.get_by_text("Are you sure")).to_be_visible()

        # Cancel and Delete buttons should be present
        expect(page.get_by_role("button", name="Cancel")).to_be_visible()
        expect(
            page.locator("#modal-container").get_by_role("button", name="Delete Project")
        ).to_be_visible()


class TestResponsiveLayout:
    """Tests for responsive design."""

    @pytest.mark.django_db(transaction=True)
    def test_mobile_viewport(self, page: Page, live_server, project) -> None:
        """UI works on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{live_server.url}/projects/{project.pk}/")

        # Core elements should still be visible - use heading
        expect(page.get_by_role("heading", name=project.name)).to_be_visible()

        # Tabs should be visible
        expect(page.get_by_role("button", name=re.compile("Assets"))).to_be_visible()
