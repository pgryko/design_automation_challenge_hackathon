"""
Tests for core models.
"""

import pytest

from core.models import ContextDocument, DesignAsset, GenerationRequest, Project


@pytest.mark.django_db
class TestProject:
    """Tests for the Project model."""

    def test_create_project(self):
        """Test creating a project."""
        project = Project.objects.create(
            name="My Project",
            description="Test description",
        )
        assert project.name == "My Project"
        assert project.description == "Test description"
        assert project.pk is not None

    def test_project_str(self, project):
        """Test project string representation."""
        assert str(project) == "Test Project"

    def test_project_ordering(self, db):
        """Test projects are ordered by updated_at descending."""
        p1 = Project.objects.create(name="First")
        p2 = Project.objects.create(name="Second")

        # Update p1 to make it more recent
        p1.name = "First Updated"
        p1.save()

        projects = list(Project.objects.all())
        assert projects[0] == p1
        assert projects[1] == p2


@pytest.mark.django_db
class TestDesignAsset:
    """Tests for the DesignAsset model."""

    def test_asset_type_choices(self):
        """Test asset type choices are defined."""
        choices = DesignAsset.AssetType.choices
        assert len(choices) == 5
        assert ("ui_screenshot", "UI Screenshot") in choices

    def test_asset_str(self, project):
        """Test asset string representation."""
        asset = DesignAsset(
            project=project,
            filename="test.png",
            asset_type=DesignAsset.AssetType.UI_SCREENSHOT,
        )
        assert "test.png" in str(asset)
        assert "UI Screenshot" in str(asset)


@pytest.mark.django_db
class TestContextDocument:
    """Tests for the ContextDocument model."""

    def test_doc_type_choices(self):
        """Test document type choices are defined."""
        choices = ContextDocument.DocType.choices
        assert len(choices) == 4
        assert ("spec", "Feature Specification") in choices

    def test_document_str(self, project):
        """Test document string representation."""
        doc = ContextDocument(
            project=project,
            title="My Spec",
            doc_type=ContextDocument.DocType.SPEC,
        )
        assert "My Spec" in str(doc)


@pytest.mark.django_db
class TestGenerationRequest:
    """Tests for the GenerationRequest model."""

    def test_status_choices(self):
        """Test status choices are defined."""
        choices = GenerationRequest.Status.choices
        assert len(choices) == 4
        assert ("pending", "Pending") in choices
        assert ("completed", "Completed") in choices

    def test_output_type_choices(self):
        """Test output type choices are defined."""
        choices = GenerationRequest.OutputType.choices
        assert len(choices) == 4
        assert ("ui_mockup", "UI Mockup") in choices

    def test_generation_request_defaults(self, project):
        """Test generation request has correct defaults."""
        gen = GenerationRequest.objects.create(
            project=project,
            prompt="Test prompt",
        )
        assert gen.status == GenerationRequest.Status.PENDING
        assert gen.progress == 0
        assert gen.num_variations == 3
        assert gen.output_type == GenerationRequest.OutputType.UI_MOCKUP
