pub mod app;

// Optionally re-export common types for easier access by library users
pub use app::formatter::OutputGenerator;
pub use app::models::RuntimeConfig;
pub use app::scanner::Scanner;

pub use app::config::build_config;
