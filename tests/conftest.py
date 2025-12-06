"""
Pytest configuration and fixtures.
"""

import os

import pytest

# Allow Django ORM in async context for Playwright tests
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from core.models import Project


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        description="A test project for unit tests",
    )


# Playwright fixtures
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture
def live_server(live_server):
    """Django live server fixture for e2e tests."""
    return live_server
