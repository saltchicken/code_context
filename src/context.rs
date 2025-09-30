use anyhow::Result;
use ignore::{DirEntry, WalkBuilder};
use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;

/// Analyzes a directory to provide context about its structure and contents,
/// respecting .gitignore rules. Data is loaded lazily upon request.
pub struct CodeContext {
    start_path: PathBuf,
    extensions: Vec<String>,
    // Private attributes to cache results, populated on first request.
    file_paths: Option<Vec<PathBuf>>,
    dir_tree: Option<String>,
}

impl CodeContext {
    /// Initializes the CodeContext object.
    pub fn new(start_path: PathBuf, extensions: Vec<String>) -> Self {
        Self {
            start_path,
            extensions,
            file_paths: None,
            dir_tree: None,
        }
    }

    /// Returns the directory structure as a formatted string.
    // CHANGE: Return an owned String to release the mutable borrow.
    pub fn get_directory_tree_string(&mut self) -> Result<String> {
        self.walk_and_collect()?;
        Ok(self.dir_tree.clone().unwrap_or_default())
    }

    /// Returns the contents of all targeted files as a single formatted string.
    pub fn get_file_contents_string(&mut self) -> Result<String> {
        self.walk_and_collect()?;
        let mut output_blocks = Vec::new();
        if let Some(paths) = &self.file_paths {
            for file_path in paths {
                let relative_path = file_path.strip_prefix(&self.start_path).unwrap_or(file_path);
                let content = match fs::read_to_string(file_path) {
                    Ok(c) => c,
                    Err(e) => {
                        output_blocks.push(format!(
                            "<file path=\"{}\" error=\"true\">Error reading file: {}</file>",
                            relative_path.display(),
                            e
                        ));
                        continue;
                    }
                };

                let file_block = format!(
                    "<file path=\"{}\">\n{}\n</file>",
                    relative_path.display(),
                    content
                );
                output_blocks.push(file_block);
            }
        }
        Ok(output_blocks.join("\n\n"))
    }

    /// Constructs the complete context as a structured string.
    pub fn get_full_context(&mut self) -> Result<String> {
        // This now works because the borrow from the first call ends immediately.
        let tree_str = self.get_directory_tree_string()?;
        if tree_str.is_empty() {
            return Ok(String::new());
        }
        let files_str = self.get_file_contents_string()?;

        Ok(format!(
            "<directory_structure>\n{}\n</directory_structure>\n\n<file_contents>\n{}\n</file_contents>",
            tree_str, files_str
        ))
    }

    /// Walks the directory tree once to populate both the file paths list
    /// and the directory tree structure. This is the primary I/O operation.
    fn walk_and_collect(&mut self) -> Result<()> {
        if self.file_paths.is_some() {
            return Ok(()); // Already populated
        }
        
        // --- This implementation is also improved for efficiency ---

        // 1. Walk the filesystem ONCE and collect all entries into memory.
        let entries: Vec<DirEntry> = WalkBuilder::new(&self.start_path)
            .build()
            .filter_map(Result::ok)
            .collect();
        
        // 2. Determine which files to include based on extensions.
        let included_files: BTreeSet<PathBuf> = entries
            .iter()
            .filter(|e| e.path().is_file())
            .filter(|e| {
                self.extensions.is_empty() || self.extensions.iter().any(|ext| {
                    e.path().to_string_lossy().ends_with(ext)
                })
            })
            .map(|e| e.path().to_path_buf())
            .collect();

        // 3. Build the directory tree string from the in-memory list.
        let mut tree_lines = Vec::new();
        for entry in &entries {
            if entry.depth() == 0 {
                continue; // Skip the root directory itself.
            }

            let path = entry.path();
            let name = path.file_name().unwrap_or_default().to_string_lossy();
            let indent = "    ".repeat(entry.depth() - 1);
            
            if path.is_dir() {
                // Only include directories that contain at least one of our target files.
                if included_files.iter().any(|f| f.starts_with(path)) {
                     tree_lines.push(format!("{}/{}", indent, name));
                }
            } else if included_files.contains(path) {
                tree_lines.push(format!("{}{}", indent, name));
            }
        }

        self.file_paths = Some(included_files.into_iter().collect());
        self.dir_tree = Some(tree_lines.join("\n"));

        Ok(())
    }
}
