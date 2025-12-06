# Session Improvements - December 6, 2025

## Completed Tasks

### 1. Lint Fixes
- Fixed 2 ruff lint issues:
  - Import sorting (auto-fixed)
  - Replaced `try-except-pass` with `contextlib.suppress(OSError)` in `core/services/document.py`

### 2. Generated Carveout Demo Outputs
Created `scripts/generate_demo.py` script that generates:
- `result/carveout/landing_hero_v1.png` (526KB) - SaaS landing page hero
- `result/carveout/mobile_fitness_v1.png` (869KB) - Mobile fitness app screen
- `result/carveout/pricing_table_v1.png` (506KB) - SaaS pricing table

Updated `result/README.md` with documentation for new outputs.

### 3. Added Service Tests (19 tests)
Created `tests/test_services.py` with tests for:
- **DocumentService**:
  - `test_supported_extensions_includes_common_formats`
  - `test_text_extensions_defined`
  - `test_docling_extensions_defined`
  - `test_get_supported_extensions_returns_sorted_list`
  - `test_extract_content_txt_file`
  - `test_extract_content_md_file`
  - `test_extract_content_unsupported_file_raises_error`
  - `test_extract_content_empty_txt_file`
  - `test_extract_content_pdf_uses_docling`

- **GeminiService**:
  - `test_init_with_defaults`
  - `test_get_headers_includes_auth`
  - `test_get_mime_type_png`
  - `test_get_mime_type_jpg`
  - `test_get_mime_type_gif`
  - `test_get_mime_type_default`

- **GeminiServiceAsync**:
  - `test_generate_image_success`
  - `test_generate_image_api_error`
  - `test_extract_style_success`
  - `test_refine_image_success`

### 4. Added View Integration Tests (19 tests)
Created `tests/test_views.py` with tests for:
- **Index**: `test_index_returns_200`, `test_index_lists_projects`
- **Projects**: CRUD operations (create, detail, edit, delete)
- **Assets**: upload, delete
- **Documents**: create with text, create with file, delete
- **Generation**: status, results
- **Downloads**: single output, ZIP, 404 handling

### 5. Configuration Updates
- Added `pytest-asyncio>=0.24.0` to dev dependencies
- Added `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "function"` to pytest config

## Test Summary
**48 tests total** - All passing:
- 10 model tests (existing)
- 19 service tests (new)
- 19 view tests (new)

## Files Modified
- `core/services/document.py` - contextlib.suppress fix
- `pyproject.toml` - pytest-asyncio, asyncio config
- `result/README.md` - carveout documentation
- `tests/test_services.py` - new
- `tests/test_views.py` - new
- `scripts/generate_demo.py` - new
