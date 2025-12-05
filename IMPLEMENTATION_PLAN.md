# Design Automation Challenge - Implementation Plan

## Overview

Build an AI-powered design assistant that learns from existing designs and generates new mockups/visuals in the same style using Django, HTMX, and Gemini 3 Pro (via OpenRouter).

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend Framework | Django 5.x | Familiar, batteries-included, fast to develop |
| API Layer | Django Ninja | Type-safe, fast, auto-generated OpenAPI docs |
| Frontend | HTMX + Alpine.js | Minimal JS, server-driven interactivity |
| Styling | Tailwind CSS | Rapid UI development, utility-first |
| AI Model | Gemini 3 Pro via OpenRouter | Vision + image generation in one model |
| Database | SQLite (dev) / PostgreSQL (prod) | Simple for hackathon, easy migration |
| Storage | Local filesystem (Django media) | Fastest for development |
| Real-time | Server-Sent Events (SSE) | Progress streaming without WebSocket complexity |

---

## Data Models

### Project
The top-level container for a design project.

```python
class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    style_summary = models.TextField(blank=True)  # Aggregated style from all assets
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### DesignAsset
Uploaded reference designs (UI screenshots, style guides, brand images).

```python
class DesignAsset(models.Model):
    class AssetType(models.TextChoices):
        UI_SCREENSHOT = 'ui_screenshot', 'UI Screenshot'
        STYLE_GUIDE = 'style_guide', 'Style Guide'
        BRAND_IMAGE = 'brand_image', 'Brand Image'
        MARKETING = 'marketing', 'Marketing Material'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assets')
    image = models.ImageField(upload_to='assets/%Y/%m/')
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    filename = models.CharField(max_length=255)
    extracted_style = models.JSONField(default=dict)  # Gemini's style analysis
    extracted_description = models.TextField(blank=True)  # Human-readable style summary
    created_at = models.DateTimeField(auto_now_add=True)
```

### ContextDocument
Supporting documents (specs, guidelines, requirements).

```python
class ContextDocument(models.Model):
    class DocType(models.TextChoices):
        SPEC = 'spec', 'Feature Specification'
        GUIDELINE = 'guideline', 'UX/UI Guideline'
        REQUIREMENTS = 'requirements', 'Requirements Document'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/%Y/%m/', blank=True)
    content = models.TextField(blank=True)  # For pasted text
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)  # AI-extracted key points
    created_at = models.DateTimeField(auto_now_add=True)
```

### GenerationRequest
A request to generate new designs.

```python
class GenerationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    class OutputType(models.TextChoices):
        UI_MOCKUP = 'ui_mockup', 'UI Mockup'
        FLOW_DIAGRAM = 'flow_diagram', 'Flow Diagram'
        MARKETING_BANNER = 'marketing_banner', 'Marketing Banner'
        BOTH = 'both', 'Both UI & Flow'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='generations')
    prompt = models.TextField()
    output_type = models.CharField(max_length=20, choices=OutputType.choices, default=OutputType.UI_MOCKUP)
    num_variations = models.IntegerField(default=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.IntegerField(default=0)  # 0-100
    progress_message = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # For refinement workflow
    parent_request = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    refinement_prompt = models.TextField(blank=True)
```

### GeneratedOutput
Individual generated images.

```python
class GeneratedOutput(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    request = models.ForeignKey(GenerationRequest, on_delete=models.CASCADE, related_name='outputs')
    image = models.ImageField(upload_to='generated/%Y/%m/')
    variation_number = models.IntegerField()
    output_type = models.CharField(max_length=20, choices=GenerationRequest.OutputType.choices)
    metadata = models.JSONField(default=dict)  # dimensions, format, generation params
    consistency_score = models.FloatField(null=True)  # Optional: AI-scored style match
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## API Endpoints (Django Ninja)

### Projects
```
GET    /api/projects/                    # List all projects
POST   /api/projects/                    # Create project
GET    /api/projects/{id}/               # Get project details
PUT    /api/projects/{id}/               # Update project
DELETE /api/projects/{id}/               # Delete project
POST   /api/projects/{id}/analyze-style/ # Re-analyze all assets, update style_summary
```

### Design Assets
```
GET    /api/projects/{id}/assets/        # List assets for project
POST   /api/projects/{id}/assets/        # Upload asset (triggers style extraction)
DELETE /api/assets/{id}/                 # Delete asset
```

### Context Documents
```
GET    /api/projects/{id}/documents/     # List documents
POST   /api/projects/{id}/documents/     # Upload/create document
DELETE /api/documents/{id}/              # Delete document
```

### Generation
```
POST   /api/projects/{id}/generate/      # Start generation (returns request_id)
GET    /api/generations/{id}/            # Get generation status + outputs
GET    /api/generations/{id}/stream/     # SSE endpoint for progress
POST   /api/generations/{id}/refine/     # Refine a generation (creates new request)
```

### Downloads
```
GET    /api/outputs/{id}/download/       # Download single output as PNG
GET    /api/generations/{id}/download/   # Download all outputs as ZIP
```

---

## Core Services

### 1. GeminiService (`services/gemini.py`)

Handles all communication with OpenRouter/Gemini API.

```python
class GeminiService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.0-flash-exp:free"  # Or gemini-3-pro-image-preview

    async def analyze_image(self, image_path: str) -> dict:
        """
        Analyze a design asset and extract style information.
        Returns structured JSON with colors, typography, spacing, etc.
        """
        pass

    async def generate_design(
        self,
        prompt: str,
        style_context: str,
        document_context: str,
        output_type: str,
        reference_images: list[str] = None
    ) -> bytes:
        """
        Generate a new design image based on prompt and context.
        Returns raw image bytes (PNG).
        """
        pass

    async def refine_design(
        self,
        original_image: str,
        refinement_prompt: str,
        style_context: str
    ) -> bytes:
        """
        Refine an existing design based on user feedback.
        """
        pass

    async def score_consistency(
        self,
        generated_image: str,
        reference_images: list[str]
    ) -> float:
        """
        Score how well a generated image matches the reference style (0-100).
        """
        pass
```

### 2. StyleService (`services/style.py`)

Manages style extraction and aggregation.

```python
class StyleService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini = gemini_service

    async def extract_style(self, asset: DesignAsset) -> dict:
        """
        Extract style information from a single asset.
        Updates asset.extracted_style and asset.extracted_description.
        """
        pass

    async def aggregate_project_style(self, project: Project) -> str:
        """
        Combine style information from all project assets.
        Updates project.style_summary with coherent description.
        """
        pass

    def build_style_context(self, project: Project) -> str:
        """
        Build the style context string for generation prompts.
        """
        pass
```

### 3. GenerationService (`services/generation.py`)

Orchestrates the generation workflow.

```python
class GenerationService:
    def __init__(self, gemini_service: GeminiService, style_service: StyleService):
        self.gemini = gemini_service
        self.style = style_service

    async def start_generation(
        self,
        request: GenerationRequest,
        progress_callback: Callable[[int, str], None]
    ) -> list[GeneratedOutput]:
        """
        Execute the full generation workflow:
        1. Build context from project assets and documents
        2. Generate N variations
        3. Save outputs
        4. Optionally score consistency
        """
        pass

    async def refine_generation(
        self,
        original_output: GeneratedOutput,
        refinement_prompt: str,
        progress_callback: Callable[[int, str], None]
    ) -> GeneratedOutput:
        """
        Create a refined version of an existing output.
        """
        pass
```

---

## Prompt Templates

### Style Extraction Prompt
```
Analyze this UI design image and extract detailed style information.

Return a JSON object with the following structure:
{
  "colors": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "text": "#hex",
    "additional": ["#hex", ...]
  },
  "typography": {
    "heading_style": "description",
    "body_style": "description",
    "font_weights": ["regular", "medium", "bold"],
    "estimated_sizes": {"heading": "24-32px", "body": "14-16px"}
  },
  "spacing": {
    "overall_feel": "tight|moderate|airy",
    "padding_pattern": "description",
    "grid_system": "description if apparent"
  },
  "components": {
    "buttons": "description of button styles",
    "cards": "description of card styles",
    "inputs": "description of input field styles",
    "icons": "description of icon style"
  },
  "visual_style": {
    "design_system": "flat|material|neumorphic|glassmorphism|other",
    "border_radius": "none|subtle|moderate|rounded|pill",
    "shadows": "none|subtle|moderate|prominent",
    "borders": "none|subtle|prominent"
  },
  "mood": ["professional", "modern", "minimal", etc],
  "summary": "2-3 sentence summary of the overall design language"
}
```

### Generation System Prompt
```
You are an expert UI/UX designer specializing in creating designs that precisely match existing brand styles.

Your task is to generate new design assets that are INDISTINGUISHABLE from the reference designs in terms of visual style.

CRITICAL REQUIREMENTS:
1. EXACT color matching - use only colors from the provided palette
2. CONSISTENT typography - match font styles, weights, and sizing patterns
3. MATCHING spacing - maintain the same density and padding patterns
4. IDENTICAL component styles - buttons, cards, inputs must look the same
5. COHERENT visual language - shadows, borders, roundness must match

You will receive:
- A style guide extracted from reference designs
- Any context documents (specs, guidelines)
- The user's specific request

Generate designs that look like they were created by the same designer as the references.
```

### Generation User Prompt Template
```
STYLE GUIDE:
{style_summary}

DETAILED STYLE CONTEXT:
{concatenated_asset_descriptions}

CONTEXT DOCUMENTS:
{document_summaries}

USER REQUEST:
{user_prompt}

OUTPUT TYPE: {output_type}

Please generate a {output_type} that:
1. Follows the exact visual style described above
2. Addresses the user's specific request
3. Uses realistic placeholder content where needed
4. Is production-ready in terms of layout and composition
```

---

## Frontend Structure (HTMX + Alpine.js)

### Page Templates

```
templates/
├── base.html                    # Base template with Tailwind, HTMX, Alpine
├── components/
│   ├── navbar.html
│   ├── sidebar.html
│   ├── toast.html               # Notification component
│   └── loading.html             # Loading spinner
├── projects/
│   ├── list.html                # Project grid/list
│   ├── detail.html              # Project detail with tabs
│   ├── create_modal.html        # HTMX modal for new project
│   └── partials/
│       ├── project_card.html    # Single project card
│       └── project_list.html    # HTMX-swappable project list
├── assets/
│   ├── upload_zone.html         # Drag-drop upload area
│   ├── asset_grid.html          # Asset thumbnails
│   └── partials/
│       ├── asset_card.html      # Single asset with analysis
│       └── style_summary.html   # Aggregated style display
├── documents/
│   ├── list.html                # Document list
│   ├── upload_form.html         # Upload/paste form
│   └── partials/
│       └── document_item.html
├── generate/
│   ├── form.html                # Generation prompt form
│   ├── progress.html            # SSE-updated progress display
│   ├── results.html             # Generated outputs grid
│   └── partials/
│       ├── output_card.html     # Single output with actions
│       ├── refinement_form.html # Inline refinement input
│       └── progress_bar.html    # Animated progress bar
└── history/
    └── list.html                # Past generations timeline
```

### Key HTMX Patterns

#### Asset Upload with Analysis
```html
<form hx-post="/api/projects/{{ project.id }}/assets/"
      hx-encoding="multipart/form-data"
      hx-target="#asset-grid"
      hx-swap="beforeend"
      hx-indicator="#upload-spinner">
    <input type="file" name="image" accept="image/*" multiple>
    <select name="asset_type">...</select>
    <button type="submit">Upload</button>
</form>

<!-- Auto-updates style summary after upload -->
<div id="style-summary"
     hx-get="/api/projects/{{ project.id }}/style-summary/"
     hx-trigger="assetUploaded from:body">
    {{ project.style_summary }}
</div>
```

#### Generation with SSE Progress
```html
<form hx-post="/api/projects/{{ project.id }}/generate/"
      hx-target="#generation-results"
      hx-swap="innerHTML"
      @submit="startProgressStream()">
    <textarea name="prompt" placeholder="Describe what you want to generate..."></textarea>
    <select name="output_type">...</select>
    <input type="number" name="num_variations" value="3" min="1" max="4">
    <button type="submit">Generate</button>
</form>

<div id="progress-container" x-show="generating">
    <div id="progress-bar" style="width: 0%"></div>
    <p id="progress-message"></p>
</div>

<div id="generation-results"></div>

<script>
function startProgressStream() {
    const eventSource = new EventSource(`/api/generations/${requestId}/stream/`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        document.getElementById('progress-bar').style.width = `${data.progress}%`;
        document.getElementById('progress-message').textContent = data.message;

        if (data.status === 'completed') {
            eventSource.close();
            htmx.trigger('#generation-results', 'load');
        }
    };
}
</script>
```

#### Refinement Inline
```html
<div class="output-card" x-data="{ refining: false }">
    <img src="{{ output.image.url }}" alt="Generated design">
    <div class="actions">
        <a :href="'/api/outputs/{{ output.id }}/download/'" download>Download PNG</a>
        <button @click="refining = true">Refine</button>
    </div>

    <div x-show="refining" x-cloak>
        <form hx-post="/api/generations/{{ output.request.id }}/refine/"
              hx-target="closest .output-card"
              hx-swap="afterend">
            <input type="hidden" name="source_output_id" value="{{ output.id }}">
            <input type="text" name="refinement_prompt"
                   placeholder="Make the buttons larger...">
            <button type="submit">Apply</button>
            <button type="button" @click="refining = false">Cancel</button>
        </form>
    </div>
</div>
```

---

## Implementation Phases

### Phase 1: Foundation (Day 1 Morning)
**Goal**: Basic project structure and database setup

- [ ] Initialize Django project with proper structure
- [ ] Configure settings (database, media, static files)
- [ ] Install dependencies (django-ninja, pillow, httpx, python-dotenv)
- [ ] Create all models with migrations
- [ ] Set up basic admin interface
- [ ] Configure Tailwind CSS with Django
- [ ] Create base template with HTMX and Alpine.js
- [ ] Implement basic project CRUD (list, create, detail views)

**Deliverable**: Can create projects and see them in a list

### Phase 2: Asset Management (Day 1 Afternoon)
**Goal**: Upload assets and extract style via Gemini

- [ ] Implement GeminiService with OpenRouter integration
- [ ] Create style extraction prompt and parsing
- [ ] Build asset upload endpoint with drag-drop UI
- [ ] Auto-analyze uploaded assets on save
- [ ] Display extracted style information per asset
- [ ] Implement StyleService.aggregate_project_style()
- [ ] Show aggregated style summary on project page

**Deliverable**: Upload images → see extracted style description

### Phase 3: Document Support (Day 1 Evening)
**Goal**: Add context documents for better generation

- [ ] Implement document upload (PDF, TXT, MD)
- [ ] Add text paste option for quick context
- [ ] Extract key points from documents (Gemini summary)
- [ ] Display documents with summaries in project view
- [ ] Include document context in style aggregation

**Deliverable**: Upload docs → see them inform style context

### Phase 4: Generation Core (Day 2 Morning)
**Goal**: Generate designs from prompts

- [ ] Build generation prompt template system
- [ ] Implement GenerationService.start_generation()
- [ ] Create generation request form UI
- [ ] Implement SSE endpoint for progress streaming
- [ ] Display progress bar with status messages
- [ ] Save generated images to GeneratedOutput
- [ ] Show results grid with download buttons

**Deliverable**: Enter prompt → see generated designs

### Phase 5: Polish & Export (Day 2 Afternoon)
**Goal**: Refinement workflow and exports

- [ ] Implement refinement workflow (regenerate with feedback)
- [ ] Add batch download as ZIP
- [ ] Create generation history view
- [ ] Implement consistency scoring (optional)
- [ ] Add error handling and user feedback
- [ ] Polish UI with loading states and transitions

**Deliverable**: Full working prototype

### Phase 6: Demo Prep (Day 2 Evening)
**Goal**: Prepare for presentation

- [ ] Pre-generate results for example prompts (DQAI, Carveout)
- [ ] Add demo mode toggle (uses cached results)
- [ ] Write README with setup instructions
- [ ] Create `/result/` folder with generated outputs
- [ ] Test full workflow end-to-end
- [ ] Prepare demo script

**Deliverable**: Demo-ready application

---

## File Structure

```
design_automation_challenge_hackathon/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── IMPLEMENTATION_PLAN.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── admin.py
│   ├── api.py                    # Django Ninja API routes
│   ├── views.py                  # HTML views for HTMX
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini.py             # OpenRouter/Gemini client
│   │   ├── style.py              # Style extraction & aggregation
│   │   └── generation.py         # Generation orchestration
│   │
│   └── templates/
│       └── core/
│           ├── base.html
│           ├── index.html        # Landing/home page
│           ├── projects/
│           ├── assets/
│           ├── documents/
│           ├── generate/
│           └── components/
│
├── static/
│   ├── css/
│   │   └── styles.css            # Tailwind output
│   ├── js/
│   │   └── app.js                # Minimal custom JS
│   └── images/
│       └── logo.svg
│
├── media/                        # Uploaded files (gitignored)
│   ├── assets/
│   ├── documents/
│   └── generated/
│
├── result/                       # Required: Example outputs for submission
│   ├── dqai/
│   └── carveout/
│
└── tailwind.config.js
```

---

## Environment Variables

```env
# .env.example

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenRouter API
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Optional: For production
DATABASE_URL=sqlite:///db.sqlite3
```

---

## Dependencies

```txt
# requirements.txt

# Core Django
Django>=5.0
django-ninja>=1.0
pillow>=10.0

# HTTP Client
httpx>=0.25

# Environment
python-dotenv>=1.0

# Development
django-debug-toolbar>=4.0

# Optional: For document processing
pypdf>=3.0
python-docx>=1.0

# Optional: For better async
uvicorn>=0.24
gunicorn>=21.0
```

---

## Key Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenRouter API key

# Database
python manage.py migrate
python manage.py createsuperuser

# Development
python manage.py runserver

# Tailwind (if using standalone)
npx tailwindcss -i ./static/css/input.css -o ./static/css/styles.css --watch
```

---

## Demo Script

1. **Create Project**: "Mobile Banking App Redesign"
2. **Upload Assets**: 3-4 existing UI screenshots from a banking app
3. **Show Style Extraction**: Point out color palette, typography detected
4. **Upload Document**: Paste feature requirements for "new payment flow"
5. **Generate**: "Create a 3-screen payment flow: amount entry, confirmation, success"
6. **Show Progress**: SSE updates in real-time
7. **Review Results**: 3 variations, all matching the uploaded style
8. **Refine**: "Make the confirm button more prominent"
9. **Download**: Export as PNG
10. **Run Example Prompts**: DQAI and Carveout flows

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Asset upload works | Drag-drop, shows in grid |
| Style extraction runs | JSON parsed, summary shown |
| Generation completes | < 60s for 3 variations |
| Style consistency | Visually matches reference designs |
| Export works | PNG download, ZIP for batch |
| SSE streaming | Progress updates smoothly |
| Example prompts | Results saved in /result/ |
| Error handling | Graceful failures, user feedback |

---

## Risk Mitigations

1. **API Rate Limits**: Queue generations, implement backoff
2. **Slow Generation**: Show engaging progress, pre-cache demo results
3. **Poor Quality**: Always generate 3+ variations, add regenerate button
4. **Large Files**: Client-side resize before upload (max 2MB)
5. **Demo Failure**: Pre-generate all demo results, toggle demo mode
