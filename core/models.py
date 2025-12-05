"""
Database models for the Design Automation Challenge.
"""

import uuid

from django.db import models
from django.urls import reverse


class Project(models.Model):
    """
    A design project containing assets, documents, and generations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    style_summary = models.TextField(
        blank=True,
        help_text="Aggregated style description from all assets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("core:project_detail", kwargs={"pk": self.pk})


class DesignAsset(models.Model):
    """
    An uploaded design reference (UI screenshot, style guide, brand image).
    """

    class AssetType(models.TextChoices):
        UI_SCREENSHOT = "ui_screenshot", "UI Screenshot"
        STYLE_GUIDE = "style_guide", "Style Guide"
        BRAND_IMAGE = "brand_image", "Brand Image"
        MARKETING = "marketing", "Marketing Material"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    image = models.ImageField(upload_to="assets/%Y/%m/")
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.UI_SCREENSHOT,
    )
    filename = models.CharField(max_length=255)
    extracted_style = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured style data extracted by AI",
    )
    extracted_description = models.TextField(
        blank=True,
        help_text="Human-readable style description",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.get_asset_type_display()})"


class ContextDocument(models.Model):
    """
    A supporting document (specs, guidelines, requirements).
    """

    class DocType(models.TextChoices):
        SPEC = "spec", "Feature Specification"
        GUIDELINE = "guideline", "UX/UI Guideline"
        REQUIREMENTS = "requirements", "Requirements Document"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True)
    content = models.TextField(blank=True, help_text="For pasted text content")
    doc_type = models.CharField(
        max_length=20,
        choices=DocType.choices,
        default=DocType.OTHER,
    )
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, help_text="AI-extracted key points")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()})"


class GenerationRequest(models.Model):
    """
    A request to generate new design assets.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class OutputType(models.TextChoices):
        UI_MOCKUP = "ui_mockup", "UI Mockup"
        FLOW_DIAGRAM = "flow_diagram", "Flow Diagram"
        MARKETING_BANNER = "marketing_banner", "Marketing Banner"
        BOTH = "both", "Both UI & Flow"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="generations",
    )
    prompt = models.TextField(help_text="User's generation request")
    output_type = models.CharField(
        max_length=20,
        choices=OutputType.choices,
        default=OutputType.UI_MOCKUP,
    )
    num_variations = models.PositiveIntegerField(default=3)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    progress = models.PositiveIntegerField(
        default=0,
        help_text="Progress percentage (0-100)",
    )
    progress_message = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # For refinement workflow
    parent_request = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="refinements",
    )
    refinement_prompt = models.TextField(
        blank=True,
        help_text="Additional refinement instructions",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Generation {self.id} ({self.get_status_display()})"


class GeneratedOutput(models.Model):
    """
    An individual generated image from a generation request.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        GenerationRequest,
        on_delete=models.CASCADE,
        related_name="outputs",
    )
    image = models.ImageField(upload_to="generated/%Y/%m/")
    variation_number = models.PositiveIntegerField()
    output_type = models.CharField(
        max_length=20,
        choices=GenerationRequest.OutputType.choices,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (dimensions, format, etc.)",
    )
    consistency_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI-scored style consistency (0-100)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["variation_number"]

    def __str__(self):
        return f"Output {self.variation_number} for {self.request_id}"
