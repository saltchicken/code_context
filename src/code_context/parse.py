import pathspec
from pathlib import Path

class CodeContext:
    """
    Analyzes a directory to provide context about its structure and contents,
    respecting .gitignore rules. Data is loaded lazily upon request.
    """
    DEFAULT_IGNORED = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

    # MODIFIED: Updated the constructor signature to accept 'only_files'.
    def __init__(self, start_path: str = ".", extensions: list[str] | None = None, include_in_tree_only: list[str] | None = None, only_files: list[str] | None = None):
        """
        Initializes the CodeContext object.

        Args:
            start_path (str): The root directory to start the analysis from.
            extensions (list[str] | None): A list of file extensions to include for content.
            include_in_tree_only (list[str] | None): A list of filenames to show in the tree but not in the content.
            only_files (list[str] | None): A specific list of files to get content from, superseding extensions.
        """
        self.start_path = Path(start_path).resolve()
        self.extensions = extensions or []
        self.include_in_tree_only = set(include_in_tree_only or [])
        # ADDED: Store the list of specific files for content.
        self.only_files = only_files or []
        self.gitignore_spec = self._load_gitignore()

        # Private attributes to cache results. They are populated by properties.
        self._file_paths: list[Path] | None = None
        self._dir_tree: list[str] | None = None

    # -------------------------------------------------------------------------
    # Public Properties for Lazy Loading   
    # -------------------------------------------------------------------------

    @property
    def file_paths(self) -> list[Path]:
        """Lazily finds and returns all relevant file paths for content."""
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
        # Sort file paths to ensure consistent output
        for file_path in sorted(self.file_paths):
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

            # Only include the file contents block if there are files to show
            if files_str:
                return (
                    "<directory_structure>\n"
                    f"{tree_str}\n"
                    "</directory_structure>\n\n"
                    "<file_contents>\n"
                    f"{files_str}\n"
                    "</file_contents>"
                )
            else:
                 return (
                    "<directory_structure>\n"
                    f"{tree_str}\n"
                    "</directory_structure>"
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
        if any(part in self.DEFAULT_IGNORED for part in path.parts):
            return True
        if self.gitignore_spec:
            relative_path = path.relative_to(self.start_path)
            if self.gitignore_spec.match_file(str(relative_path)):
                return True
        return False

    # MODIFIED: Reworked the walking logic to handle the new '--only-files' rule.
    def _walk_and_collect(self) -> None:
        """
        Walks the directory tree once to populate both the file paths list (for content)
        and the directory tree structure string list.
        """
        self._file_paths = []
        self._dir_tree = []
        
        # For efficient lookup, convert only_files to a set of relative paths.
        only_files_relative = {str(Path(p).as_posix()) for p in self.only_files}

        for root_str, dirs, files in self.start_path.walk():
            root = Path(root_str)
            
            # Filter and sort directories in place.
            dirs[:] = sorted([d for d in dirs if not self._is_ignored(root / d)])
            
            if root == self.start_path:
                depth = 0
            else:
                depth = len(root.relative_to(self.start_path).parts)
                indent = "    " * (depth - 1)
                self._dir_tree.append(f"{indent}{root.name}/")

            file_indent = "    " * depth
            for file_name in sorted(files):
                file_path = root / file_name
                if self._is_ignored(file_path):
                    continue
                
                relative_path_str = str(file_path.relative_to(self.start_path).as_posix())
                
                # --- Tree Logic ---
                # A file appears in the tree if it matches extensions OR is an 'include_in_tree_only' file.
                # This logic is independent of which file contents are included.
                if file_name in self.include_in_tree_only or (self.extensions and file_path.suffix in self.extensions):
                    self._dir_tree.append(f"{file_indent}{file_name}")

                # --- Content Logic ---
                # Decide if the file's content should be included.
                if self.only_files:
                    # If --only-files is used, it's the sole source of truth for content.
                    if relative_path_str in only_files_relative:
                        self._file_paths.append(file_path)
                else:
                    # Otherwise, use extensions, but exclude 'tree_only' files.
                    if self.extensions and file_path.suffix in self.extensions:
                        if file_name not in self.include_in_tree_only:
                            self._file_paths.append(file_path)
