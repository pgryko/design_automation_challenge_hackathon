# Example Prompt Outputs

This folder contains AI-generated design outputs for the **Design Automation Challenge - HACKATHON@DAVOS**.

All outputs were generated using the Design Automation tool with the example prompts from the challenge specification.

## Folder Structure

```
result/
├── dqai/                           # DQAI (Data Quality AI) screens
│   ├── 01_project_systems.png      # SAP systems associated with project
│   ├── 02_installation_progress.png # JiVS IMP installation progress
│   ├── 03_data_transfer.png        # Data transfer monitoring view
│   ├── 04_analysis_results.png     # Analysis dashboard with trend chart
│   └── 05_run_history.png          # Run history table
├── carveout/                       # Carveout operation screens
│   ├── 01_project_systems.png      # Source systems overview
│   ├── 02_data_transfer.png        # Data transfer status
│   ├── 03_carveout_definition.png  # Carveout scope definition
│   ├── 04_subset_validation.png    # Subset preview and validation
│   ├── 05_carveout_results.png     # Results with trend chart
│   └── 06_run_history.png          # Carveout operation history
└── README.md                       # This file
```

---

## DQAI (Data Quality AI) Outputs

Based on the challenge prompt: *"Simulate the lifecycle where SAP systems are first associated with the project, an installation is initiated for the target environment, and during this phase, a simulated progress experience is represented. After the environment is 'ready,' present a data transfer view in which transfer items transition from Pending to Success. When transfers have completed, show a results experience that compares metrics over time, including at least one trend chart and a run history."*

### Screen 1: Project Systems
**File**: `dqai/01_project_systems.png`

Shows the OCC dashboard with SAP systems associated with a project:
- Navigation sidebar (Dashboard, Projects, Systems, Transfers, Analysis)
- SAP system cards with connection status badges
- System configuration options

### Screen 2: Installation Progress
**File**: `dqai/02_installation_progress.png`

JiVS IMP installation wizard showing:
- Multi-step progress indicator (Provision → Install → Configure → Prepare → Validate)
- Current step details with progress bar
- Log output and time estimates
- Reflects mediator app and export handler setup

### Screen 3: Data Transfer
**File**: `dqai/03_data_transfer.png`

Data transfer monitoring view showing:
- Summary stats (Total Tables, Completed, In Progress, Pending)
- Transfer table with status badges (Success/In Progress/Pending)
- Real-time progress indication
- Table names, record counts, timestamps

### Screen 4: Analysis Results
**File**: `dqai/04_analysis_results.png`

Data Quality AI analysis dashboard with:
- **Trend Chart**: Data Quality Score over time (line chart)
- Summary metrics (Quality Score, Records Analyzed, Issues Found)
- Issue breakdown by category
- Export and action buttons

### Screen 5: Run History
**File**: `dqai/05_run_history.png`

Analysis run history table showing:
- Past runs with timestamps, duration, status
- Quality scores per run
- Filter and search capabilities
- Repeatable analysis tracking

---

## Carveout Outputs

Based on the challenge prompt: *"Show a Carveout experience that defines a filtered subset (e.g., organizational units, time slices), previews/validates the subset (record counts, affected entities), and optionally indicates readiness to forward the carved data to a downstream target. Include at least one trend chart (e.g., carved volume over time) and a simple run history of carve operations."*

### Screen 1: Project Systems
**File**: `carveout/01_project_systems.png`

Carveout project overview showing:
- Source SAP systems with record counts
- Target destination configuration
- Project phase and timeline

### Screen 2: Data Transfer
**File**: `carveout/02_data_transfer.png`

Data transfer progress for carveout:
- Transfer table with source tables and status
- Record counts and progress indicators
- Overall completion percentage

### Screen 3: Carveout Definition
**File**: `carveout/03_carveout_definition.png`

Carveout scope configuration with:
- **Organizational Units**: Company code selection
- **Time Slice**: Date range picker
- **Personnel Area**: Checkbox filters
- Scope preview (estimated records, tables, data size)

### Screen 4: Subset Validation
**File**: `carveout/04_subset_validation.png`

Subset preview and validation showing:
- Validation status with warnings
- Record counts by entity type
- Referential integrity checks
- Readiness indicator for execution

### Screen 5: Carveout Results
**File**: `carveout/05_carveout_results.png`

Carveout execution results with:
- **Trend Chart**: Carved data volume over time
- Latest run summary (records, duration, status)
- Target system status
- Forward and export options

### Screen 6: Run History
**File**: `carveout/06_run_history.png`

Carveout operation history showing:
- Past carveout runs with scope and status
- Record counts and durations
- Target forwarding status
- Audit trail for compliance

---

## Style Context

All screens follow the **OCC/JiVS Enterprise** design language:
- **Colors**: Primary blue (#1E40AF), Success green (#059669), Warning amber (#D97706)
- **Typography**: Inter/system sans-serif, professional hierarchy
- **Components**: Data tables, status badges, progress indicators, sidebar navigation
- **Visual Style**: Enterprise SaaS, data-focused, professional German engineering quality

---

## Regenerating Outputs

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# Generate outputs
uv run python scripts/generate_challenge_outputs.py
```

---

## Key Features Demonstrated

1. **Design Asset Ingestion**: Style context extracted and applied consistently
2. **Knowledge Integration**: OCC/JiVS domain context informs all generations
3. **Prompt-Based Generation**: Natural language prompts → complete UI screens
4. **AI-Driven Output**: Gemini 2.0 Flash generates production-quality mockups
5. **Consistency**: All screens share unified enterprise design language
6. **Exportable**: PNG format, ready for presentation or further design work
