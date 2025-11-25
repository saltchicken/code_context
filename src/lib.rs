// ‼️ New file: This serves as the root for the library target.
// It exposes the app module so external crates (and our own binary) can use it.

pub mod app;

// Optionally re-export common types for easier access by library users
pub use app::formatter::OutputGenerator;
pub use app::models::RuntimeConfig;
pub use app::scanner::Scanner;
