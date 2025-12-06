# Design Automation Challenge

AI-powered design assistant that learns from existing designs and generates new mockups/visuals in the same style.

## Features

- **Design Asset Ingestion**: Upload UI screenshots, style guides, and brand images
- **Style Extraction**: AI analyzes uploaded assets to understand visual style (colors, typography, spacing, components)
- **Context Documents**: Add specifications and guidelines (PDF, DOCX, PPTX, TXT, MD, HTML)
- **Prompt-Based Generation**: Describe what you want, AI generates matching designs
- **Multiple Variations**: Generate 1-3 variations per request
- **Refinement Workflow**: Iteratively improve generated designs with feedback
- **Export**: Download individual PNGs or all variations as ZIP

## Tech Stack

- **Backend**: Django 6.0 + Django Ninja
- **Frontend**: HTMX + Alpine.js + Tailwind CSS
- **AI**: Gemini via OpenRouter API
- **Database**: SQLite (development) / PostgreSQL (production)

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+ (for Tailwind CSS)
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd design_automation_challenge_hackathon

# Install Python dependencies
uv sync

# Install Node dependencies (for Tailwind)
npm install

# Copy environment file and configure
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run database migrations
uv run python manage.py migrate

# Create a superuser (optional)
uv run python manage.py createsuperuser

# Build Tailwind CSS
npm run tailwind:build

# Run the development server
uv run python manage.py runserver
```

### Development

```bash
# Run Tailwind in watch mode (in a separate terminal)
npm run tailwind:watch

# Run the Django development server
uv run python manage.py runserver

# Run linting and formatting
uv run ruff check --fix .
uv run ruff format .

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

## Project Structure

```
design_automation_challenge_hackathon/
├── config/              # Django project settings
├── core/                # Main application
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   ├── urls.py          # URL routing
│   ├── admin.py         # Admin configuration
│   └── services/        # Business logic (AI services)
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   └── core/            # App-specific templates
├── static/              # Static files (CSS, JS)
├── media/               # User uploads (gitignored)
└── result/              # Generated outputs for submission
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | (required in production) |
| `OPENROUTER_API_KEY` | OpenRouter API key | (required) |
| `OPENROUTER_MODEL` | AI model to use | `google/gemini-2.0-flash-exp:free` |

## License

MIT
