"""
Views for the core app.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import ContextDocument, DesignAsset, GenerationRequest, Project


@require_GET
def index(request):
    """Home page - list all projects."""
    projects = Project.objects.all()
    return render(request, "core/index.html", {"projects": projects})


@require_http_methods(["GET", "POST"])
def project_create(request):
    """Create a new project."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            project = Project.objects.create(name=name, description=description)

            # If HTMX request, return the updated project list
            if request.headers.get("HX-Request"):
                projects = Project.objects.all()
                return render(
                    request, "core/partials/project_list.html", {"projects": projects}
                )

            return redirect("core:project_detail", pk=project.pk)

    # GET request - return the modal form
    return render(request, "core/projects/create_modal.html")


@require_GET
def project_detail(request, pk):
    """View project details."""
    project = get_object_or_404(Project, pk=pk)
    return render(request, "core/projects/detail.html", {"project": project})


@require_http_methods(["GET", "POST"])
def project_edit(request, pk):
    """Edit a project."""
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            project.name = name
            project.description = description
            project.save()

            if request.headers.get("HX-Request"):
                return render(
                    request, "core/projects/detail.html", {"project": project}
                )

            return redirect("core:project_detail", pk=project.pk)

    return render(request, "core/projects/edit_modal.html", {"project": project})


@require_http_methods(["DELETE"])
def project_delete(request, pk):
    """Delete a project."""
    project = get_object_or_404(Project, pk=pk)
    project.delete()

    if request.headers.get("HX-Request"):
        # Redirect to index via HTMX
        response = HttpResponse()
        response["HX-Redirect"] = "/"
        return response

    return redirect("core:index")


@require_POST
def asset_upload(request, project_pk):
    """Upload design assets."""
    project = get_object_or_404(Project, pk=project_pk)
    asset_type = request.POST.get("asset_type", "ui_screenshot")

    uploaded_files = request.FILES.getlist("images")

    for uploaded_file in uploaded_files:
        DesignAsset.objects.create(
            project=project,
            image=uploaded_file,
            asset_type=asset_type,
            filename=uploaded_file.name,
        )
        # TODO: Trigger async style extraction via Gemini

    # Return updated asset grid
    return render(request, "core/projects/tabs/assets.html", {"project": project})


@require_http_methods(["DELETE"])
def asset_delete(request, pk):
    """Delete a design asset."""
    asset = get_object_or_404(DesignAsset, pk=pk)
    project = asset.project
    asset.delete()

    # Return updated asset grid
    if request.headers.get("HX-Request"):
        return render(request, "core/projects/tabs/assets.html", {"project": project})

    return redirect("core:project_detail", pk=project.pk)


@require_POST
def document_create(request, project_pk):
    """Create a context document."""
    project = get_object_or_404(Project, pk=project_pk)

    title = request.POST.get("title", "").strip()
    doc_type = request.POST.get("doc_type", "other")
    content = request.POST.get("content", "").strip()
    uploaded_file = request.FILES.get("file")

    if title:
        doc = ContextDocument.objects.create(
            project=project,
            title=title,
            doc_type=doc_type,
            content=content,
        )
        if uploaded_file:
            doc.file = uploaded_file
            doc.save()
        # TODO: Trigger async summary extraction via Gemini

    # Return updated document list
    return render(request, "core/projects/tabs/documents.html", {"project": project})


@require_http_methods(["DELETE"])
def document_delete(request, pk):
    """Delete a context document."""
    doc = get_object_or_404(ContextDocument, pk=pk)
    project = doc.project
    doc.delete()

    if request.headers.get("HX-Request"):
        return render(
            request, "core/projects/tabs/documents.html", {"project": project}
        )

    return redirect("core:project_detail", pk=project.pk)


@require_POST
def generate(request, project_pk):
    """Start a new generation request."""
    project = get_object_or_404(Project, pk=project_pk)

    prompt = request.POST.get("prompt", "").strip()
    output_type = request.POST.get("output_type", "ui_mockup")
    num_variations = int(request.POST.get("num_variations", 3))

    if prompt:
        generation = GenerationRequest.objects.create(
            project=project,
            prompt=prompt,
            output_type=output_type,
            num_variations=num_variations,
            status=GenerationRequest.Status.PENDING,
        )
        # TODO: Trigger async generation via Gemini

        # For now, return a placeholder response
        return render(
            request,
            "core/partials/generation_pending.html",
            {"generation": generation, "project": project},
        )

    return render(request, "core/projects/tabs/generate.html", {"project": project})
