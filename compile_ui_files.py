import argparse
import os
import subprocess
from datetime import datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class UIFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        if event.is_directory:
            return

        if ".ui" not in os.path.basename(event.src_path):
            return

        # Extract the base file path without the temporary suffix
        ui_path: str = event.src_path.split(".ui")[0] + ".ui"

        if not os.path.exists(ui_path):
            print(f"Valid .ui file not found for: {event.src_path}")
            return

        ui_name = os.path.basename(ui_path).split(".ui")[0]
        output_path = os.path.join(os.path.dirname(ui_path), f"{ui_name}_UI.py")

        # Compile the .ui file
        try:
            subprocess.run(["pyuic6", ui_path, "-o", output_path], check=True)
            print(
                f"{datetime.now().isoformat()} - Compiled: {ui_name}.ui -> {ui_name}_UI.py"
            )
        except subprocess.CalledProcessError as e:
            print(f"{datetime.now().isoformat()} - Error compiling {ui_path}: {e}")
        except FileNotFoundError:
            print(
                f"{datetime.now().isoformat()} - Error: pyuic6 command not found. Ensure it's installed and accessible in PATH."
            )


def compile_ui_files_once(directories: list[str]):
    """Run the compilation once for all .ui files."""
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".ui"):
                    file_path = os.path.join(root, file)
                    handler = UIFileHandler()
                    handler.process(
                        type(
                            "Event",
                            (object,),
                            {"src_path": file_path, "is_directory": False},
                        )
                    )


def watch_directories(directories: list[str]):
    """Watch directories for changes to .ui files."""
    observer = Observer()
    for directory in directories:
        event_handler = UIFileHandler()
        observer.schedule(event_handler, directory, recursive=True)

    print(f"{datetime.now().isoformat()} - Watching directories for changes...")
    observer.start()
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        print(f"{datetime.now().isoformat()} - Stopping directory watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile PyQt6 .ui files. Use --watch to monitor changes."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run the script in watch mode to monitor for file changes.",
    )
    args = parser.parse_args()

    directories_to_watch = [
        r"C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\ui",
    ]

    if args.watch:
        watch_directories(directories_to_watch)
    else:
        print(f"{datetime.now().isoformat()} - Compiling .ui files once...")
        compile_ui_files_once(directories_to_watch)
        print(f"{datetime.now().isoformat()} - Done.")
