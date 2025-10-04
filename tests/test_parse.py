import pytest
from pathlib import Path
from code_context.parse import CodeContext

# A pytest fixture to create a sample directory structure for testing
@pytest.fixture
def test_project_dir(tmp_path: Path) -> Path:
    """Creates a temporary directory with a sample project structure."""
    # Create directories
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / ".venv").mkdir()

    # Create files
    (tmp_path / "src/main.py").write_text("print('hello')")
    (tmp_path / "src/utils.py").write_text("# A utility module")
    (tmp_path / "docs/guide.md").write_text("# Guide")
    (tmp_path / "config.json").write_text('{"key": "value"}')
    (tmp_path / ".gitignore").write_text("*.log\n.venv/\n")
    (tmp_path / "secret.log").write_text("secret info")
    
    return tmp_path

# --- Tests for the CodeContext class ---

def test_include_by_extension(test_project_dir):
    """Test including files based on their extension."""
    context = CodeContext(
        start_path=str(test_project_dir),
        include_extensions=[".py"]
    )
    output = context.get_full_context()
    
    assert "src/main.py" in output
    assert "src/utils.py" in output
    assert "docs/guide.md" not in output
    assert "config.json" not in output

def test_exclude_by_gitignore(test_project_dir):
    """Test that .gitignore rules are respected."""
    context = CodeContext(
        start_path=str(test_project_dir),
        include_extensions=[".py", ".log"]
    )
    output = context.get_full_context()
    
    # secret.log should be excluded by .gitignore
    assert "secret.log" not in output
    # .venv should be excluded entirely
    assert ".venv" not in output

def test_exclude_by_patterns(test_project_dir):
    """Test the custom exclude_patterns functionality."""
    context = CodeContext(
        start_path=str(test_project_dir),
        include_extensions=[".py", ".md"],
        exclude_patterns=["docs/*"] # Exclude the docs directory
    )
    output = context.get_full_context()

    assert "src/main.py" in output
    assert "docs/guide.md" not in output # Should be excluded by the pattern

def test_tree_only_output(test_project_dir):
    """Test that get_directory_tree_string() only shows the tree."""
    context = CodeContext(
        start_path=str(test_project_dir),
        include_extensions=[".py"]
    )
    tree_output = context.get_directory_tree_string()
    
    # Check for file/dir names in the tree
    assert "src/" in tree_output
    assert "main.py" in tree_output
    # Ensure file content is not present
    assert "print('hello')" not in tree_output
