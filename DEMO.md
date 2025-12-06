# Design Automation Demo Script

Step-by-step guide for demonstrating the AI Design Automation tool.

## Prerequisites

Ensure the following are installed and configured:
- Python 3.13+
- Node.js 18+
- uv package manager
- OpenRouter API key in `.env` file

## Quick Start

```bash
# 1. Install dependencies
uv sync
npm install

# 2. Build CSS
npm run tailwind:build

# 3. Run migrations
uv run python manage.py migrate

# 4. Start server
uv run python manage.py runserver

# 5. Open browser
open http://localhost:8000
```

---

## Demo Walkthrough

### Step 1: Create a New Project

1. Click **"New Project"** on the homepage
2. Enter project details:
   - **Name**: "Marketing Website Redesign"
   - **Description**: "Modern landing page design for SaaS product"
3. Click **"Create Project"**

### Step 2: Upload Context Documents (Optional)

1. Click the **"Documents"** tab
2. Upload a specification document:
   - Drag and drop a PDF, DOCX, or TXT file
   - Or click to browse files
3. The document content will be extracted and used as context for generation

**Supported formats**: PDF, DOCX, PPTX, TXT, MD, HTML

### Step 3: Upload Design Assets (Optional)

1. Click the **"Assets"** tab
2. Upload reference images:
   - UI screenshots for style reference
   - Brand images or logos
   - Style guides
3. Select the asset type from the dropdown
4. Click **"Analyze All Assets"** to extract visual style

**Supported formats**: PNG, JPG, GIF (up to 10MB each)

### Step 4: Generate Designs

1. Click the **"Generate"** tab
2. Fill in the generation form:
   - **Prompt**: Describe what you want to generate
   - **Type**: Select generation type (UI Mockup, Marketing Visual, etc.)
   - **Variations**: Choose 1-3 variations
3. Click **"Generate"**
4. Watch the progress indicator as AI generates designs

**Example prompts**:
```
Generate a modern dashboard screen with:
- Sidebar navigation (Home, Analytics, Settings)
- Main content area with data cards
- Header with search and user profile
- Clean, minimalist aesthetic
```

```
Create a hero section for a SaaS landing page:
- Bold headline with subtext
- CTA buttons (Start Free Trial, Learn More)
- Product screenshot or illustration
- Gradient background
```

### Step 5: Review Results

1. Generated images appear in a grid
2. Each variation shows:
   - Thumbnail preview (click to enlarge)
   - Download button (individual PNG)
   - Refine button (for iterations)
3. Click **"Download All (ZIP)"** to get all variations

### Step 6: Refine Designs

1. Find a generated image you want to improve
2. Click the **"Refine"** button
3. Enter refinement instructions:
   - "Make the colors darker"
   - "Add more whitespace"
   - "Change the button style to rounded"
4. Click **"Apply"**
5. New refined version is generated

### Step 7: View History

1. Click the **"History"** tab
2. See all past generations for the project
3. Refinements show a "Refinement" badge
4. Re-download or further refine any previous output

---

## Demo Scenarios

### Scenario A: Dashboard Design

**Goal**: Generate a SaaS dashboard UI

1. Create project: "Analytics Dashboard"
2. Generate with prompt:
   ```
   Create a data analytics dashboard with:
   - Left sidebar navigation
   - Top metrics cards showing KPIs
   - Line chart for trends
   - Recent activity list
   - Dark mode theme
   ```
3. Refine: "Add a date range picker in the header"

### Scenario B: Landing Page Hero

**Goal**: Generate a marketing landing page section

1. Create project: "Product Launch"
2. Upload brand guidelines PDF (optional)
3. Generate with prompt:
   ```
   Design a hero section for a productivity app:
   - Headline: "Work Smarter, Not Harder"
   - Subheadline explaining key benefit
   - Email signup form
   - Floating product mockup
   - Purple gradient background
   ```
4. Refine: "Make the CTA button more prominent with orange color"

### Scenario C: Mobile App Screens

**Goal**: Generate mobile UI mockups

1. Create project: "Fitness App"
2. Generate with prompt:
   ```
   Design a mobile fitness app home screen:
   - Bottom navigation bar
   - Today's workout card
   - Progress ring showing weekly goal
   - Quick action buttons
   - iOS style design
   ```

---

## Talking Points

### Key Features

- **AI-Powered Generation**: Uses Gemini to create complete UI mockups from text
- **Context-Aware**: Incorporates uploaded documents and style references
- **Iterative Refinement**: Improve designs through conversation-style feedback
- **Multiple Variations**: Generate 1-3 options per request
- **Export Ready**: Download individual PNGs or batch ZIP

### Technical Highlights

- **Backend**: Django 6.0 with Django Ninja API
- **Frontend**: HTMX + Alpine.js for reactive UI without JavaScript framework
- **AI**: Gemini 2.0 Flash via OpenRouter API
- **Document Processing**: Docling for PDF/DOCX text extraction
- **Real-time Progress**: Server-Sent Events for generation status

### Use Cases

1. **Rapid Prototyping**: Quickly visualize UI concepts before development
2. **Design Exploration**: Generate multiple variations to explore directions
3. **Client Presentations**: Create mockups for proposals and pitches
4. **Style Consistency**: Upload references to maintain brand consistency
5. **Iterative Design**: Refine outputs based on feedback

---

## Troubleshooting

### CSS Not Loading
```bash
npm run tailwind:build
```

### Database Errors
```bash
uv run python manage.py migrate
```

### API Errors
- Check `.env` has valid `OPENROUTER_API_KEY`
- Verify API quota is available

### Generation Timeout
- Default timeout is 5 minutes
- Complex prompts may take longer
- Check server logs for errors
