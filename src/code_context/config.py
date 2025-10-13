import logging
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def load_presets() -> dict:
    """
    Loads presets from the user's configuration file at ~/.config/code_context/presets.toml.
    """
    user_config_path = Path.home() / ".config" / "code_context" / "presets.toml"
    if user_config_path.is_file():
        try:
            presets_text = user_config_path.read_text(encoding='utf-8')
            return tomllib.loads(presets_text)
        except Exception as e:
            logging.warning(f"⚠️ Could not parse user presets at {user_config_path}: {e}")
    return {}

def resolve_config(project_name: str | None, cli_args: object) -> dict:
    """
    Resolves the final configuration by merging presets with CLI arguments.
    
    Args:
        project_name: The name of the project directory (e.g., 'code_context').
        cli_args: The parsed arguments object from argparse.
    
    Returns:
        A dictionary with the final 'include', 'exclude', and 'include_in_tree' lists.
    """
    presets = load_presets()
    preset_values = presets.get(project_name, {}) if project_name else {}

    # Combine preset and command-line arguments, with CLI args taking precedence.
    # The dict.fromkeys method is a simple way to remove duplicates while preserving order.
    final_include = list(dict.fromkeys(preset_values.get('include', []) + (cli_args.include or [])))
    final_exclude = list(dict.fromkeys(preset_values.get('exclude', []) + (cli_args.exclude or [])))
    final_include_in_tree = list(dict.fromkeys(preset_values.get('include_in_tree', []) + (cli_args.include_in_tree or [])))
    
    return {
        "include": final_include,
        "exclude": final_exclude,
        "include_in_tree": final_include_in_tree,
    }
