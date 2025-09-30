use anyhow::Result;
use clap::Parser;
use git2::build::RepoBuilder;
use git2::FetchOptions;
use std::path::PathBuf;
use tempfile::TempDir;

mod context;
use context::CodeContext;

/// Gather and display a codebase context, useful for LLMs.
/// By default, it shows the directory tree and all file contents.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// List of file extensions to include (e.g., rs js html).
    extensions: Vec<String>,

    /// URL of a Git repository to clone and analyze.
    #[arg(long)]
    repo: Option<String>,

    /// Show only the directory tree structure.
    #[arg(long)]
    tree: bool,

    /// Show only the contents of the files.
    #[arg(long)]
    files: bool,

    /// Copy the generated context to the clipboard instead of printing.
    #[arg(long)]
    copy: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Ensure extensions start with a dot, matching the Python script's logic.
    let extensions: Vec<String> = args
        .extensions
        .iter()
        .map(|ext| format!(".{}", ext.trim_start_matches('.')))
        .collect();

    // Keep temp_dir in scope so it's cleaned up on drop.
    let temp_dir: Option<TempDir> = if args.repo.is_some() {
        Some(tempfile::Builder::new().prefix("code_context_").tempdir()?)
    } else {
        None
    };

    let start_path = match &args.repo {
        Some(repo_url) => {
            let path = temp_dir.as_ref().unwrap().path();
            println!("🔄 Cloning repository from {}...", repo_url);

            let mut fo = FetchOptions::new();
            fo.depth(1); // --depth=1 for a shallow clone

            let mut builder = RepoBuilder::new();
            builder.fetch_options(fo);

            builder.clone(repo_url, path)?;
            println!("✅ Clone successful.");
            path.to_path_buf()
        }
        None => PathBuf::from("."),
    };

    let mut context = CodeContext::new(start_path, extensions);
    let mut output_parts = Vec::new();

    let has_specific_requests = args.tree || args.files;

    if has_specific_requests {
        if args.tree {
            output_parts.push(context.get_directory_tree_string()?.to_string());
        }
        if args.files {
            output_parts.push(context.get_file_contents_string()?);
        }
    } else {
        // Default behavior: get the full context
        output_parts.push(context.get_full_context()?);
    }

    let final_output = output_parts.join("\n\n");

    if args.copy {
        let mut clipboard = arboard::Clipboard::new()?;
        clipboard.set_text(&final_output)?;
        println!("✅ Context copied to clipboard.");
    } else if !final_output.is_empty() {
        println!("{}", final_output);
    } else {
        println!("No content found for the specified extensions.");
    }

    if let Some(dir) = temp_dir {
        println!("🧹 Cleaned up temporary directory: {}", dir.path().display());
    }

    Ok(())
}
