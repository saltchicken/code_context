import subprocess
import sys
from pathlib import Path

# Use the same fixture from the unit tests
from test_parse import test_project_dir

def run_cli_command(cwd: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Helper function to run the code_context CLI in a specific directory."""
    # Use 'sys.executable -m code_context' to ensure we run the installed script
    # from the current environment.
    command = [sys.executable, "-m", "code_context"] + args
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=cwd, # Run the command from our test project directory
        check=True
    )

def test_cli_basic_run(test_project_dir):
    """Test a basic CLI run with extension inclusion."""
    result = run_cli_command(test_project_dir, ["--include-extensions", "py", "json"])
    stdout = result.stdout
    
    assert "src/main.py" in stdout
    assert "config.json" in stdout
    assert "docs/guide.md" not in stdout
    assert "print('hello')" in stdout # Check for file content

def test_cli_tree_only_flag(test_project_dir):
    """Test the --tree flag to ensure only the structure is printed."""
    result = run_cli_command(test_project_dir, ["--include-extensions", "py", "--tree"])
    stdout = result.stdout
    
    assert "src/" in stdout
    assert "main.py" in stdout
    assert "print('hello')" not in stdout # Content should be absent

def test_cli_preset(test_project_dir):
    """Test using a built-in preset."""
    # The 'python' preset should ignore .venv and include .py files.
    result = run_cli_command(test_project_dir, ["--preset", "python"])
    stdout = result.stdout

    assert "src/main.py" in stdout
    assert ".venv" not in stdout
    assert "config.json" not in stdout

def test_cli_error_on_no_includes(test_project_dir):
    """Test that the CLI exits with an error if no include rules are provided."""
    command = [sys.executable, "-m", "code_context"]
    # We expect this to fail, so we don't use check=True
    result = subprocess.run(command, capture_output=True, text=True, cwd=test_project_dir)
    
    assert result.returncode != 0
    assert "must be provided" in result.stderr
