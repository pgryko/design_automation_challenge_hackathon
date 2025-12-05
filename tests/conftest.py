"""
Pytest configuration and fixtures.
"""

import pytest

from core.models import Project


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        description="A test project for unit tests",
    )
