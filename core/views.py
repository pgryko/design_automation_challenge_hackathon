"""
Views for the core app.
"""

import asyncio
import json
import logging
import threading

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import ContextDocument, DesignAsset, GenerationRequest, Project
from .services import GeminiService, StyleService
from .services.gemini import GeminiServiceError

logger = logging.getLogger(__name__)


def _run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""

    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


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
    created_assets = []

    for uploaded_file in uploaded_files:
        asset = DesignAsset.objects.create(
            project=project,
            image=uploaded_file,
            asset_type=asset_type,
            filename=uploaded_file.name,
        )
        created_assets.append(asset)

    # Trigger background style extraction for each asset
    for asset in created_assets:
        # Run async extraction in background thread
        _run_async_in_thread(_extract_asset_style_background(asset.pk))

    # Return updated asset grid
    project.refresh_from_db()
    return render(request, "core/projects/tabs/assets.html", {"project": project})


async def _extract_asset_style_background(asset_pk):
    """Background task to extract style from an asset."""
    try:
        from core.models import DesignAsset

        asset = await DesignAsset.objects.select_related("project").aget(pk=asset_pk)
        style_service = StyleService()
        await style_service.extract_asset_style(asset)

        # Update project aggregated style
        await style_service.aggregate_project_style(asset.project)
        logger.info(f"Background style extraction completed for asset {asset_pk}")
    except Exception as e:
        logger.error(f"Background style extraction failed for asset {asset_pk}: {e}")


@require_POST
def analyze_asset(request, pk):
    """Manually trigger style analysis for a single asset."""
    asset = get_object_or_404(DesignAsset, pk=pk)

    # Run sync wrapper for async extraction
    try:
        result = asyncio.run(_analyze_asset_sync(asset))
        return JsonResponse({"success": True, "style": result})
    except GeminiServiceError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


async def _analyze_asset_sync(asset):
    """Helper to run async style extraction."""
    style_service = StyleService()
    result = await style_service.extract_asset_style(asset)
    await style_service.aggregate_project_style(asset.project)
    return result


@require_POST
def analyze_project(request, pk):
    """Analyze all unanalyzed assets in a project."""
    project = get_object_or_404(Project, pk=pk)

    try:
        results = asyncio.run(_analyze_project_sync(project))

        if request.headers.get("HX-Request"):
            project.refresh_from_db()
            return render(
                request, "core/projects/tabs/assets.html", {"project": project}
            )

        return JsonResponse({"success": True, "analyzed": len(results)})
    except GeminiServiceError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


async def _analyze_project_sync(project):
    """Helper to run async project analysis."""
    style_service = StyleService()
    return await style_service.analyze_all_assets(project)


@require_http_methods(["DELETE"])
def asset_delete(request, pk):
    """Delete a design asset."""
    asset = get_object_or_404(DesignAsset, pk=pk)
    project = asset.project
    asset.delete()

    # Re-aggregate style after deletion
    asyncio.run(_reaggregate_style(project))

    # Return updated asset grid
    if request.headers.get("HX-Request"):
        project.refresh_from_db()
        return render(request, "core/projects/tabs/assets.html", {"project": project})

    return redirect("core:project_detail", pk=project.pk)


async def _reaggregate_style(project):
    """Re-aggregate project style after asset changes."""
    style_service = StyleService()
    await style_service.aggregate_project_style(project)


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

        # Generate summary for the document
        if content:
            asyncio.run(_summarize_document(doc))

    # Return updated document list
    return render(request, "core/projects/tabs/documents.html", {"project": project})


async def _summarize_document(doc):
    """Generate a summary for a document."""
    try:
        gemini = GeminiService()

        prompt = f"""Summarize the following document in 2-3 sentences, focusing on key design requirements, guidelines, or specifications:

{doc.content[:3000]}"""

        # Use text completion for summarization
        payload = {
            "model": gemini.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.5,
        }

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{gemini.base_url}/chat/completions",
                headers=gemini._get_headers(),
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                summary = data["choices"][0]["message"]["content"]
                doc.summary = summary
                await doc.asave()
                logger.info(f"Generated summary for document {doc.pk}")

    except Exception as e:
        logger.error(f"Failed to summarize document {doc.pk}: {e}")


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

        # Start generation in background thread
        _run_async_in_thread(_run_generation_background(generation.pk))

        # Return pending state with SSE connection
        return render(
            request,
            "core/partials/generation_pending.html",
            {"generation": generation, "project": project},
        )

    return render(request, "core/projects/tabs/generate.html", {"project": project})


async def _run_generation_background(generation_pk):
    """Background task to run generation."""
    from datetime import datetime

    from django.core.files.base import ContentFile
    from django.utils import timezone

    from core.models import GeneratedOutput, GenerationRequest

    try:
        generation = await GenerationRequest.objects.select_related("project").aget(
            pk=generation_pk
        )

        # Update status
        generation.status = GenerationRequest.Status.PROCESSING
        generation.progress = 10
        generation.progress_message = "Preparing style context..."
        await generation.asave()

        # Build style context
        style_service = StyleService()
        style_context = style_service.build_style_context(generation.project)

        generation.progress = 20
        generation.progress_message = "Generating designs..."
        await generation.asave()

        # Generate variations
        gemini = GeminiService()
        progress_per_variation = 60 // generation.num_variations

        for i in range(generation.num_variations):
            try:
                generation.progress = 20 + (i * progress_per_variation)
                generation.progress_message = (
                    f"Generating variation {i + 1} of {generation.num_variations}..."
                )
                await generation.asave()

                # Try image generation
                try:
                    image_bytes = await gemini.generate_image(
                        prompt=generation.prompt,
                        style_context=style_context,
                    )

                    # Save generated image
                    output = GeneratedOutput(
                        request=generation,
                        variation_number=i + 1,
                        output_type=generation.output_type,
                        metadata={"generated_at": datetime.now().isoformat()},
                    )
                    output.image.save(
                        f"generation_{generation.pk}_v{i + 1}.png",
                        ContentFile(image_bytes),
                        save=False,
                    )
                    await output.asave()

                except GeminiServiceError as e:
                    # Fall back to text description if image generation fails
                    logger.warning(
                        f"Image generation failed, falling back to text: {e}"
                    )
                    text_response = await gemini.generate_with_text_response(
                        prompt=generation.prompt,
                        style_context=style_context,
                        output_type=generation.output_type,
                    )

                    output = GeneratedOutput(
                        request=generation,
                        variation_number=i + 1,
                        output_type=generation.output_type,
                        metadata={
                            "generated_at": datetime.now().isoformat(),
                            "type": "text_description",
                            "content": text_response,
                        },
                    )
                    await output.asave()

            except Exception as e:
                logger.error(f"Failed to generate variation {i + 1}: {e}")

        # Mark as completed
        generation.status = GenerationRequest.Status.COMPLETED
        generation.progress = 100
        generation.progress_message = "Generation complete!"
        generation.completed_at = timezone.now()
        await generation.asave()

        logger.info(f"Generation {generation_pk} completed successfully")

    except Exception as e:
        logger.error(f"Generation {generation_pk} failed: {e}")
        try:
            generation = await GenerationRequest.objects.aget(pk=generation_pk)
            generation.status = GenerationRequest.Status.FAILED
            generation.error_message = str(e)
            await generation.asave()
        except Exception:
            pass


@require_GET
def generation_status(request, pk):
    """Get the current status of a generation request."""
    generation = get_object_or_404(GenerationRequest, pk=pk)
    return JsonResponse(
        {
            "status": generation.status,
            "progress": generation.progress,
            "message": generation.progress_message,
            "error": generation.error_message,
        }
    )


@require_GET
def generation_stream(request, pk):
    """SSE endpoint for generation progress."""
    generation = get_object_or_404(GenerationRequest, pk=pk)

    def event_stream():
        import time

        last_progress = -1

        while True:
            # Refresh from database
            generation.refresh_from_db()

            # Send update if progress changed
            if generation.progress != last_progress:
                last_progress = generation.progress
                data = json.dumps(
                    {
                        "status": generation.status,
                        "progress": generation.progress,
                        "message": generation.progress_message,
                    }
                )
                yield f"data: {data}\n\n"

            # Check if done
            if generation.status in [
                GenerationRequest.Status.COMPLETED,
                GenerationRequest.Status.FAILED,
            ]:
                # Send final update with results
                if generation.status == GenerationRequest.Status.COMPLETED:
                    outputs = list(generation.outputs.all())
                    data = json.dumps(
                        {
                            "status": generation.status,
                            "progress": 100,
                            "message": "Complete!",
                            "outputs": [
                                {
                                    "id": str(o.pk),
                                    "url": o.image.url if o.image else None,
                                }
                                for o in outputs
                            ],
                        }
                    )
                else:
                    data = json.dumps(
                        {
                            "status": generation.status,
                            "progress": generation.progress,
                            "message": generation.error_message,
                        }
                    )
                yield f"data: {data}\n\n"
                break

            time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@require_GET
def generation_results(request, pk):
    """Get the results of a completed generation."""
    generation = get_object_or_404(GenerationRequest, pk=pk)
    project = generation.project

    return render(
        request,
        "core/partials/generation_results.html",
        {"generation": generation, "project": project},
    )
