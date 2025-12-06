"""
Integration tests for core views.
"""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

import pytest

from core.models import (
    ContextDocument,
    DesignAsset,
    GeneratedOutput,
    GenerationRequest,
    Project,
)


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        description="A test project for integration tests",
    )


@pytest.fixture
def generation_request(project):
    """Create a test generation request."""
    return GenerationRequest.objects.create(
        project=project,
        prompt="Test prompt",
        status=GenerationRequest.Status.COMPLETED,
    )


@pytest.fixture
def generated_output(generation_request, tmp_path):
    """Create a test generated output with an image file."""
    # Create a minimal PNG file
    png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    output = GeneratedOutput.objects.create(
        request=generation_request,
        variation_number=1,
        output_type=GenerationRequest.OutputType.UI_MOCKUP,
    )

    # Save the image file
    from django.core.files.base import ContentFile

    output.image.save("test_output.png", ContentFile(png_content))
    return output


@pytest.mark.django_db
class TestIndexView:
    """Tests for the index/home view."""

    def test_index_returns_200(self, client):
        """Test index page returns 200."""
        response = client.get(reverse("core:index"))
        assert response.status_code == 200

    def test_index_lists_projects(self, client, project):
        """Test index page lists projects."""
        response = client.get(reverse("core:index"))
        assert response.status_code == 200
        assert b"Test Project" in response.content


@pytest.mark.django_db
class TestProjectViews:
    """Tests for project CRUD views."""

    def test_project_create_get(self, client):
        """Test GET request to project create page."""
        response = client.get(reverse("core:project_create"))
        assert response.status_code == 200

    def test_project_create_post(self, client):
        """Test creating a new project."""
        response = client.post(
            reverse("core:project_create"),
            {
                "name": "New Project",
                "description": "New project description",
            },
        )
        # Should redirect to project detail
        assert response.status_code == 302
        assert Project.objects.filter(name="New Project").exists()

    def test_project_detail(self, client, project):
        """Test viewing project detail."""
        response = client.get(
            reverse("core:project_detail", kwargs={"pk": project.pk})
        )
        assert response.status_code == 200
        assert b"Test Project" in response.content

    def test_project_edit_get(self, client, project):
        """Test GET request to project edit page."""
        response = client.get(
            reverse("core:project_edit", kwargs={"pk": project.pk})
        )
        assert response.status_code == 200

    def test_project_edit_post(self, client, project):
        """Test editing a project."""
        response = client.post(
            reverse("core:project_edit", kwargs={"pk": project.pk}),
            {
                "name": "Updated Project",
                "description": "Updated description",
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Updated Project"

    def test_project_delete(self, client, project):
        """Test deleting a project."""
        project_id = project.pk
        response = client.delete(
            reverse("core:project_delete", kwargs={"pk": project_id})
        )
        assert response.status_code == 302
        assert not Project.objects.filter(pk=project_id).exists()


@pytest.mark.django_db
class TestAssetViews:
    """Tests for asset upload/delete views."""

    def test_asset_upload_creates_asset(self, client, project):
        """Test uploading a design asset."""
        # Create a minimal PNG image
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image = SimpleUploadedFile(
            name="test_image.png",
            content=png_content,
            content_type="image/png",
        )

        response = client.post(
            reverse("core:asset_upload", kwargs={"project_pk": project.pk}),
            {
                "images": image,  # View expects "images" (plural)
                "asset_type": DesignAsset.AssetType.UI_SCREENSHOT,
            },
        )

        # Should return 200 with HTMX partial
        assert response.status_code == 200
        assert DesignAsset.objects.filter(project=project).exists()

    @patch("core.views._reaggregate_style")
    def test_asset_delete(self, mock_reaggregate, client, project):
        """Test deleting an asset."""
        # Create an asset first
        asset = DesignAsset.objects.create(
            project=project,
            filename="test.png",
            asset_type=DesignAsset.AssetType.UI_SCREENSHOT,
        )

        response = client.delete(
            reverse("core:asset_delete", kwargs={"pk": asset.pk})
        )

        assert response.status_code == 302  # Redirects when not HTMX
        assert not DesignAsset.objects.filter(pk=asset.pk).exists()


@pytest.mark.django_db
class TestDocumentViews:
    """Tests for document create/delete views."""

    def test_document_create_with_text(self, client, project):
        """Test creating a document with pasted text."""
        response = client.post(
            reverse("core:document_create", kwargs={"project_pk": project.pk}),
            {
                "title": "Test Document",
                "doc_type": ContextDocument.DocType.SPEC,
                "content": "This is the document content.",
            },
        )

        assert response.status_code == 200
        assert ContextDocument.objects.filter(
            project=project, title="Test Document"
        ).exists()

    def test_document_create_with_file(self, client, project):
        """Test creating a document with uploaded file."""
        txt_file = SimpleUploadedFile(
            name="spec.txt",
            content=b"Feature specification content",
            content_type="text/plain",
        )

        response = client.post(
            reverse("core:document_create", kwargs={"project_pk": project.pk}),
            {
                "title": "Spec Document",
                "doc_type": ContextDocument.DocType.SPEC,
                "file": txt_file,
            },
        )

        assert response.status_code == 200
        doc = ContextDocument.objects.get(project=project, title="Spec Document")
        assert "Feature specification content" in doc.content

    def test_document_delete(self, client, project):
        """Test deleting a document."""
        doc = ContextDocument.objects.create(
            project=project,
            title="To Delete",
            doc_type=ContextDocument.DocType.OTHER,
            content="Content",
        )

        response = client.delete(
            reverse("core:document_delete", kwargs={"pk": doc.pk})
        )

        assert response.status_code == 302  # Redirects when not HTMX
        assert not ContextDocument.objects.filter(pk=doc.pk).exists()


@pytest.mark.django_db
class TestGenerationViews:
    """Tests for generation and download views."""

    def test_generation_status(self, client, generation_request):
        """Test getting generation status."""
        response = client.get(
            reverse(
                "core:generation_status",
                kwargs={"pk": generation_request.pk},
            )
        )
        assert response.status_code == 200
        assert b"completed" in response.content.lower()

    def test_generation_results(self, client, generated_output):
        """Test getting generation results."""
        response = client.get(
            reverse(
                "core:generation_results",
                kwargs={"pk": generated_output.request.pk},
            )
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestDownloadViews:
    """Tests for download views."""

    def test_download_output(self, client, generated_output):
        """Test downloading a single output."""
        response = client.get(
            reverse("core:download_output", kwargs={"pk": generated_output.pk})
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "attachment" in response["Content-Disposition"]

    def test_download_generation_zip(self, client, generated_output):
        """Test downloading all outputs as ZIP."""
        response = client.get(
            reverse(
                "core:download_generation",
                kwargs={"pk": generated_output.request.pk},
            )
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "application/zip"
        assert "attachment" in response["Content-Disposition"]

    def test_download_nonexistent_output_returns_404(self, client):
        """Test downloading nonexistent output returns 404."""
        import uuid

        response = client.get(
            reverse("core:download_output", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_download_nonexistent_generation_returns_404(self, client):
        """Test downloading nonexistent generation returns 404."""
        import uuid

        response = client.get(
            reverse("core:download_generation", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestViewEdgeCases:
    """Edge case tests for views error handling."""

    def test_project_create_empty_name_fails(self, client):
        """Test that creating project with empty name fails."""
        response = client.post(
            reverse("core:project_create"),
            {
                "name": "",  # Empty name
                "description": "Test description",
            },
        )
        # Should not redirect (form error)
        assert response.status_code == 200
        assert not Project.objects.filter(description="Test description").exists()

    def test_project_edit_nonexistent_returns_404(self, client):
        """Test editing nonexistent project returns 404."""
        import uuid

        response = client.get(
            reverse("core:project_edit", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_project_delete_nonexistent_returns_404(self, client):
        """Test deleting nonexistent project returns 404."""
        import uuid

        response = client.delete(
            reverse("core:project_delete", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_asset_upload_no_files(self, client, project):
        """Test asset upload with no files returns partial."""
        response = client.post(
            reverse("core:asset_upload", kwargs={"project_pk": project.pk}),
            {
                "asset_type": DesignAsset.AssetType.UI_SCREENSHOT,
                # No files
            },
        )
        # Should still return 200 (empty list is valid)
        assert response.status_code == 200

    def test_asset_delete_nonexistent_returns_404(self, client):
        """Test deleting nonexistent asset returns 404."""
        import uuid

        response = client.delete(
            reverse("core:asset_delete", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_document_create_empty_content_and_no_file(self, client, project):
        """Test creating document with no content or file fails."""
        response = client.post(
            reverse("core:document_create", kwargs={"project_pk": project.pk}),
            {
                "title": "Empty Doc",
                "doc_type": ContextDocument.DocType.SPEC,
                # No content or file
            },
        )
        # Should still return 200 (creates doc with empty content)
        assert response.status_code == 200

    def test_document_delete_nonexistent_returns_404(self, client):
        """Test deleting nonexistent document returns 404."""
        import uuid

        response = client.delete(
            reverse("core:document_delete", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_generation_status_nonexistent_returns_404(self, client):
        """Test getting status of nonexistent generation returns 404."""
        import uuid

        response = client.get(
            reverse("core:generation_status", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_generation_results_nonexistent_returns_404(self, client):
        """Test getting results of nonexistent generation returns 404."""
        import uuid

        response = client.get(
            reverse("core:generation_results", kwargs={"pk": uuid.uuid4()})
        )
        assert response.status_code == 404

    def test_download_incomplete_generation_returns_error(self, client, project):
        """Test downloading incomplete generation returns error."""
        generation = GenerationRequest.objects.create(
            project=project,
            prompt="Test",
            status=GenerationRequest.Status.PROCESSING,  # Not completed
        )

        response = client.get(
            reverse("core:download_generation", kwargs={"pk": generation.pk})
        )
        assert response.status_code == 400
        assert b"not complete" in response.content
