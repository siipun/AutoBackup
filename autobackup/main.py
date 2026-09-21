from .project import get_project_directory, get_project_name
from .watcher import start_watching


def main():

    project_path = get_project_directory()
    project_name = get_project_name(project_path)

    print()
    print("===================================")
    print("          AUTOBACKUP V1")
    print("===================================")
    print()
    print(f"Project: {project_name}")
    print(f"Location: {project_path}")
    print()

    start_watching(project_path)


if __name__ == "__main__":
    main()
