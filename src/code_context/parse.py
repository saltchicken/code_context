import pathspec
from pathlib import Path

class CodeContext:
    """
    Analyzes a directory to provide context about its structure and contents,
    respecting .gitignore rules and user-defined filters.
    """
    DEFAULT_IGNORED = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

    def __init__(self, start_path: str = ".", 
                 include_extensions: list[str] | None = None,
                 exclude_extensions: list[str] | None = None,
                 include_files: list[str] | None = None,
                 exclude_files: list[str] | None = None,
                 include_file_in_tree: list[str] | None = None,
                 include_extension_in_tree: list[str] | None = None,
                 exclude_patterns: list[str] | None = None):
        """
        Initializes the CodeContext object with detailed filtering rules.
        """
        self.start_path = Path(start_path).resolve()

        # --- Inclusion Rules ---
        self.include_extensions = set(include_extensions or [])
        self.include_files = {str(Path(p).as_posix()) for p in (include_files or [])}
        self.include_file_in_tree = set(include_file_in_tree or [])
        self.include_extension_in_tree = set(include_extension_in_tree or [])
        
        # --- Exclusion Rules ---
        self.exclude_extensions = set(exclude_extensions or [])
        self.exclude_files = {str(Path(p).as_posix()) for p in (exclude_files or [])}
        
        # --- Pattern-based Exclusion ---
        self.gitignore_spec = self._load_gitignore()
        self.exclude_spec = self._load_exclude_patterns(exclude_patterns)
        
        # --- Caches ---
        self._file_paths_content: list[Path] | None = None
        self._dir_tree: list[str] | None = None

    @property
    def file_paths(self) -> list[Path]:
        """Lazily finds and returns all relevant file paths for content."""
        if self._file_paths_content is None:
            self._walk_and_collect()
        return self._file_paths_content or []

    @property
    def dir_tree(self) -> list[str]:
        """Lazily generates and returns the directory tree structure."""
        if self._dir_tree is None:
            self._walk_and_collect()
        return self._dir_tree or []

    def get_directory_tree_string(self) -> str:
        """Returns the directory structure as a formatted string."""
        return "\n".join(self.dir_tree)

    def get_file_contents_string(self) -> str:
        """Returns the contents of all targeted files as a single formatted string."""
        output_blocks = []
        for file_path in sorted(self.file_paths):
            relative_path = file_path.relative_to(self.start_path)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                file_block = (
                    f'<file path="{relative_path}">\n'
                    f"{content}\n"
                    '</file>'
                )
                output_blocks.append(file_block)

            except Exception as e:
                output_blocks.append(f'<file path="{relative_path}" error="true">Error reading file: {e}</file>')
        
        return "\n\n".join(output_blocks)

    def get_full_context(self) -> str:
        """Constructs the complete context as a structured string."""
        tree_str = self.get_directory_tree_string()
        files_str = self.get_file_contents_string()

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

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """Loads .gitignore patterns from the start path."""
        gitignore_path = self.start_path / ".gitignore"
        if gitignore_path.exists():
            with gitignore_path.open("r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitignore", f)
        return None

    def _load_exclude_patterns(self, patterns: list[str] | None) -> pathspec.PathSpec | None:
        """Compiles provided exclude patterns into a PathSpec object."""
        if patterns:
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return None

    def _is_path_excluded(self, path: Path, relative_path_str: str | None = None) -> bool:
        """Checks if a given path should be excluded based on any rule."""
        if any(part in self.DEFAULT_IGNORED for part in path.parts):
            return True
        
        # Only calculate relative path if needed for file checks
        if path.is_file():
            if relative_path_str is None:
                 relative_path_str = str(path.relative_to(self.start_path).as_posix())
            if path.suffix in self.exclude_extensions:
                return True
            if relative_path_str in self.exclude_files:
                return True

        if self.gitignore_spec or self.exclude_spec:
            if relative_path_str is None:
                relative_path_str = str(path.relative_to(self.start_path).as_posix())
            
            if self.gitignore_spec and self.gitignore_spec.match_file(relative_path_str):
                return True
            
            if self.exclude_spec and self.exclude_spec.match_file(relative_path_str):
                return True

        return False

    def _walk_and_collect(self) -> None:
        """
        Walks the directory tree to populate file paths and the tree structure,
        applying all inclusion and exclusion rules.
        """
        self._file_paths_content = []
        self._dir_tree = []

        for root_str, dirs, files in self.start_path.walk():
            root = Path(root_str)
            
            dirs[:] = sorted([d for d in dirs if not self._is_path_excluded(root / d)])
            
            if root == self.start_path:
                depth = 0
            else:
                depth = len(root.relative_to(self.start_path).parts)
                indent = "    " * (depth - 1)
                self._dir_tree.append(f"{indent}{root.name}/")

            file_indent = "    " * depth
            for file_name in sorted(files):
                file_path = root / file_name
                relative_path_str = str(file_path.relative_to(self.start_path).as_posix())
                
                if self._is_path_excluded(file_path, relative_path_str):
                    continue

                is_content_candidate = (
                    relative_path_str in self.include_files or
                    (self.include_extensions and file_path.suffix in self.include_extensions)
                )

                is_tree_only = (
                    file_name in self.include_file_in_tree or
                    file_path.suffix in self.include_extension_in_tree
                )

                if is_content_candidate or is_tree_only:
                    self._dir_tree.append(f"{file_indent}{file_name}")

                if is_content_candidate and not is_tree_only:
                    self._file_paths_content.append(file_path)
