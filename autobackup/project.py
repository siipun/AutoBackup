from pathlib import Path

def get_project_directory() -> Path:
    
    return Path.cwd().resolve()

def get_project_name(project_path: Path) -> str:

    return project_path.name