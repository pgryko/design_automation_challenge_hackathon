"""
Django admin configuration for core models.
"""

from django.contrib import admin

from .models import (
    ContextDocument,
    DesignAsset,
    GeneratedOutput,
    GenerationRequest,
    Project,
)


class DesignAssetInline(admin.TabularInline):
    model = DesignAsset
    extra = 0
    readonly_fields = ["extracted_style", "extracted_description", "created_at"]


class ContextDocumentInline(admin.TabularInline):
    model = ContextDocument
    extra = 0
    readonly_fields = ["summary", "created_at"]


class GenerationRequestInline(admin.TabularInline):
    model = GenerationRequest
    extra = 0
    readonly_fields = ["status", "progress", "created_at", "completed_at"]
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "asset_count", "generation_count", "updated_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "style_summary", "created_at", "updated_at"]
    inlines = [DesignAssetInline, ContextDocumentInline, GenerationRequestInline]

    @admin.display(description="Assets")
    def asset_count(self, obj):
        return obj.assets.count()

    @admin.display(description="Generations")
    def generation_count(self, obj):
        return obj.generations.count()


@admin.register(DesignAsset)
class DesignAssetAdmin(admin.ModelAdmin):
    list_display = ["filename", "project", "asset_type", "created_at"]
    list_filter = ["asset_type", "created_at"]
    search_fields = ["filename", "project__name"]
    readonly_fields = ["id", "extracted_style", "extracted_description", "created_at"]


@admin.register(ContextDocument)
class ContextDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "doc_type", "created_at"]
    list_filter = ["doc_type", "created_at"]
    search_fields = ["title", "project__name"]
    readonly_fields = ["id", "summary", "created_at"]


class GeneratedOutputInline(admin.TabularInline):
    model = GeneratedOutput
    extra = 0
    readonly_fields = [
        "variation_number",
        "output_type",
        "consistency_score",
        "created_at",
    ]


@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "output_type", "status", "progress", "created_at"]
    list_filter = ["status", "output_type", "created_at"]
    search_fields = ["prompt", "project__name"]
    readonly_fields = [
        "id",
        "progress",
        "progress_message",
        "error_message",
        "created_at",
        "completed_at",
    ]
    inlines = [GeneratedOutputInline]


@admin.register(GeneratedOutput)
class GeneratedOutputAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "request",
        "variation_number",
        "output_type",
        "consistency_score",
    ]
    list_filter = ["output_type", "created_at"]
    readonly_fields = ["id", "metadata", "consistency_score", "created_at"]
