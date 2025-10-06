import pathspec
from pathlib import Path

class CodeContext:
    """
    Analyzes a directory to provide context about its structure and contents,
    respecting .gitignore rules and user-defined filters.
    """
    DEFAULT_IGNORED = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

    def __init__(self, start_path: str = ".",
                 include: list[str] | None = None,
                 exclude: list[str] | None = None,
                 include_in_tree: list[str] | None = None):
        """
        Initializes the CodeContext object with gitignore-style filtering rules.
        """
        self.start_path = Path(start_path).resolve()

        # --- Compile PathSpec objects from patterns ---
        self.include_spec = self._compile_spec_from_patterns(include)
        self.tree_only_spec = self._compile_spec_from_patterns(include_in_tree)
        
        # --- Exclusion Rules ---
        self.gitignore_spec = self._load_gitignore()
        self.exclude_spec = self._compile_spec_from_patterns(exclude)
        
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
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        return None

    def _compile_spec_from_patterns(self, patterns: list[str] | None) -> pathspec.PathSpec | None:
        """Compiles provided gitwildmatch patterns into a PathSpec object."""
        if patterns:
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return None

    def _is_path_excluded(self, path: Path, relative_path_str: str) -> bool:
        """Checks if a given path should be excluded based on any rule."""
        if any(part in self.DEFAULT_IGNORED for part in path.parts):
            return True
        
        if self.gitignore_spec and self.gitignore_spec.match_file(relative_path_str):
            return True
        
        if self.exclude_spec and self.exclude_spec.match_file(relative_path_str):
            return True

        return False

    def _walk_and_collect(self) -> None:
        """
        Walks the directory tree to populate file paths and the tree structure,
        applying all inclusion and exclusion rules from the compiled PathSpec objects.
        """
        self._file_paths_content = []
        self._dir_tree = []

        for root_str, dirs, files in self.start_path.walk():
            root = Path(root_str)
            relative_root_str = str(root.relative_to(self.start_path).as_posix())
            if relative_root_str == '.':
                relative_root_str = ''

            # Filter directories in-place
            dirs[:] = sorted([
                d for d in dirs 
                if not self._is_path_excluded(root / d, f"{relative_root_str}/{d}" if relative_root_str else d)
            ])
            
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

                matches_content = (
                    self.include_spec and self.include_spec.match_file(relative_path_str)
                )
                matches_tree_only = (
                    self.tree_only_spec and self.tree_only_spec.match_file(relative_path_str)
                )

                # A file appears in the tree if it matches content patterns OR tree-only patterns.
                if matches_content or matches_tree_only:
                    self._dir_tree.append(f"{file_indent}{file_name}")

                # A file's content is added only if it's a content match AND NOT a tree-only match.
                # This allows tree-only patterns to override content inclusion.
                if matches_content and not matches_tree_only:
                    self._file_paths_content.append(file_path)
