import pathspec
from pathlib import Path

class CodeContext:
    """
    Analyzes a directory to provide context about its structure and contents,
    respecting .gitignore rules. Data is loaded lazily upon request.
    """
    DEFAULT_IGNORED = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

    def __init__(self, start_path: str = ".", extensions: list[str] | None = None):
        """
        Initializes the CodeContext object.

        Args:
            start_path (str): The root directory to start the analysis from.
            extensions (list[str] | None): A list of file extensions to include (e.g., ['.py', '.js']).
                                            If None, all files are considered (after ignoring).
        """
        self.start_path = Path(start_path).resolve()
        self.extensions = extensions or []
        self.gitignore_spec = self._load_gitignore()

        # Private attributes to cache results. They are populated by properties.
        self._file_paths: list[Path] | None = None
        self._dir_tree: list[str] | None = None

    # -------------------------------------------------------------------------
    # Public Properties for Lazy Loading    
    # -------------------------------------------------------------------------

    @property
    def file_paths(self) -> list[Path]:
        """Lazily finds and returns all relevant file paths."""
        if self._file_paths is None:
            self._walk_and_collect()
        return self._file_paths or []

    @property
    def dir_tree(self) -> list[str]:
        """Lazily generates and returns the directory tree structure."""
        if self._dir_tree is None:
            self._walk_and_collect()
        return self._dir_tree or []

    # -------------------------------------------------------------------------
    # Public Methods for Generating Output Strings
    # -------------------------------------------------------------------------

    def get_directory_tree_string(self) -> str:
        """Returns the directory structure as a formatted string."""
        return "\n".join(self.dir_tree)

    def get_file_contents_string(self) -> str:
        """Returns the contents of all targeted files as a single formatted string."""
        output_blocks = []
        for file_path in self.file_paths:
            relative_path = file_path.relative_to(self.start_path)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Build the complete string for one file
                file_block = (
                    f'<file path="{relative_path}">\n'
                    f"{content}\n"
                    '</file>'
                )
                output_blocks.append(file_block)

            except Exception as e:
                output_blocks.append(f'<file path="{relative_path}" error="true">Error reading file: {e}</file>')
        
        # Join the complete blocks with two newlines for separation
        return "\n\n".join(output_blocks)

    def get_full_context(self) -> str:
            """Constructs the complete context as a structured string."""
            tree_str = self.get_directory_tree_string()
            files_str = self.get_file_contents_string()

            return (
                "<directory_structure>\n"
                f"{tree_str}\n"
                "</directory_structure>\n\n"
                "<file_contents>\n"
                f"{files_str}\n"
                "</file_contents>"
            )

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """Loads .gitignore patterns from the start path."""
        gitignore_path = self.start_path / ".gitignore"
        if gitignore_path.exists():
            with gitignore_path.open("r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitignore", f)
        return None

    def _is_ignored(self, path: Path) -> bool:
        """Checks if a given path should be ignored."""
        # Check against default ignored set
        if any(part in self.DEFAULT_IGNORED for part in path.parts):
            return True
        # Check against .gitignore patterns
        if self.gitignore_spec:
            # Use relative path for gitignore matching
            relative_path = path.relative_to(self.start_path)
            if self.gitignore_spec.match_file(str(relative_path)):
                return True
        return False

    def _walk_and_collect(self) -> None:
        """
        Walks the directory tree once to populate both the file paths list
        and the directory tree structure. This is the primary I/O operation.
        """
        self._file_paths = []
        self._dir_tree = []

        for root_str, dirs, files in self.start_path.walk():
            root = Path(root_str)
            
            # Filter directories in place to prevent traversal
            dirs[:] = [d for d in dirs if not self._is_ignored(root / d)]
            
            # Don't include the root directory itself in the tree output
            if root == self.start_path:
                depth = 0
            else:
                # Calculate depth relative to the start path
                depth = len(root.relative_to(self.start_path).parts)
                # Add the directory to the tree
                indent = "    " * (depth - 1)
                self._dir_tree.append(f"{indent}{root.name}/")

            # Add files at the correct indentation level
            file_indent = "    " * depth
            for file_name in files:
                file_path = root / file_name
                if not self._is_ignored(file_path):
                    # If extensions are specified, filter by them
                    if self.extensions and file_path.suffix not in self.extensions:
                        continue
                    
                    self._dir_tree.append(f"{file_indent}{file_name}")
                    self._file_paths.append(file_path)
