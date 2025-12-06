"""
URL configuration for the core app.
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Projects
    path("", views.index, name="index"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<uuid:pk>/", views.project_detail, name="project_detail"),
    path("projects/<uuid:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<uuid:pk>/delete/", views.project_delete, name="project_delete"),
    path(
        "projects/<uuid:pk>/delete/confirm/",
        views.project_delete_confirm,
        name="project_delete_confirm",
    ),
    # Assets
    path("projects/<uuid:project_pk>/assets/", views.asset_upload, name="asset_upload"),
    path("assets/<uuid:pk>/delete/", views.asset_delete, name="asset_delete"),
    # Documents
    path(
        "projects/<uuid:project_pk>/documents/",
        views.document_create,
        name="document_create",
    ),
    path("documents/<uuid:pk>/delete/", views.document_delete, name="document_delete"),
    # Analysis
    path("assets/<uuid:pk>/analyze/", views.analyze_asset, name="analyze_asset"),
    path("projects/<uuid:pk>/analyze/", views.analyze_project, name="analyze_project"),
    # Generation
    path("projects/<uuid:project_pk>/generate/", views.generate, name="generate"),
    path(
        "generations/<uuid:pk>/status/",
        views.generation_status,
        name="generation_status",
    ),
    path(
        "generations/<uuid:pk>/stream/",
        views.generation_stream,
        name="generation_stream",
    ),
    path(
        "generations/<uuid:pk>/results/",
        views.generation_results,
        name="generation_results",
    ),
    # Refinement and Downloads
    path(
        "outputs/<uuid:pk>/refine/",
        views.refine_output,
        name="refine_output",
    ),
    path(
        "outputs/<uuid:pk>/download/",
        views.download_output,
        name="download_output",
    ),
    path(
        "generations/<uuid:pk>/download/",
        views.download_generation,
        name="download_generation",
    ),
]
