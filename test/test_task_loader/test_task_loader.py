"""Unit test for task loading functionality. Uses the files in `./test_projects`, attempting to load tasks from each project."""

import pytest
import warnings
from pathlib import Path
from icua.utils import TaskLoader


def get_project_paths():
    """Get paths of projects to test."""
    project_paths = Path(__file__).parent / "test_projects"
    project_paths = set([p for p in project_paths.iterdir() if p.is_dir()])

    project_paths_dynamic = set(
        filter(lambda p: any([s.suffix == ".py" for s in p.iterdir()]), project_paths)
    )
    for p in project_paths_dynamic:
        warnings.warn(
            f"Failed to test project at path: {p.as_posix()} as dynamic task loading has been deprecated."
        )
    return project_paths - project_paths_dynamic


@pytest.fixture(params=get_project_paths())
def project_path(request):  # noqa
    return request.param


def test_task_loader_on_project(project_path: Path):
    """Tests the TaskLoader class by loading projects from `./test_projects`."""
    assert project_path.exists()
    loader = TaskLoader()
    loader.register_task("task", project_path)
    task = loader.load("task", [], [])  # noqa
    # TODO further validate the task output (the xml)?
