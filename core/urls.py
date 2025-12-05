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
    # Generation
    path("projects/<uuid:project_pk>/generate/", views.generate, name="generate"),
]
