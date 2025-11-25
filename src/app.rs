// ‼️ Change: specific modules are now public for library usage
pub mod cli;
pub mod config;
pub mod formatter;
pub mod models;
pub mod scanner;

use anyhow::{Context, Result};
use clap::Parser;
use std::env;
use std::path::PathBuf;

use self::cli::Cli;
use self::config::resolve_config;
use self::formatter::OutputGenerator;
use self::models::RuntimeConfig;
use self::scanner::Scanner;

// ‼️ New Function: Exposes the core logic to library users.
// This allows running the scan programmatically without CLI args.
pub fn generate(config: RuntimeConfig, root: PathBuf) -> Result<String> {
    // 4. Scan Directory
    let scanner = Scanner::new(root, &config)?;
    let entries = scanner.scan();

    if entries.is_empty() {
        return Ok(String::new());
    }

    // 5. Generate Output
    let tree_str = OutputGenerator::generate_tree(&entries);
    let final_output = if config.tree_only_output {
        format!(
            "<directory_structure>\n{}\n</directory_structure>",
            tree_str
        )
    } else {
        let content_str = OutputGenerator::generate_content(&entries);
        OutputGenerator::format_full_output(&tree_str, &content_str)
    };

    Ok(final_output)
}

/// Initializes components and orchestrates data flow (CLI Mode).
pub fn run() -> Result<()> {
    // 1. Parse Args
    let args = Cli::parse();

    // 2. Identify Project Root & Name
    let current_dir = env::current_dir().context("Failed to get current directory")?;
    // Simple heuristic: name of current folder
    let project_name = current_dir.file_name().and_then(|n| n.to_str());

    // 3. Resolve Configuration
    let config = resolve_config(args, project_name)?;

    // Validation (mirroring Python logic)
    if config.include.is_empty() && config.include_in_tree.is_empty() {
        anyhow::bail!("No include patterns provided. Please use --include (e.g., 'src/**/*.rs') or specify a preset.");
    }

    // ‼️ Change: Use the library's generate function
    let output = generate(config, current_dir)?;

    if output.is_empty() {
        log::warn!("⚠️ No content found for the specified criteria.");
        return Ok(());
    }

    // 6. Print to Stdout
    println!("{}", output);

    Ok(())
}
