import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme import set_theme


class VersionUpdater(QWidget):
    selected_version = None

    def __init__(self, initial_version):
        super().__init__()
        self.current_version = initial_version
        self.versions = self.calculate_versions(self.current_version)
        self.initUI(initial_version)

    def initUI(self, initial_version):
        self.setWindowTitle("Version Updater")

        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        button_version_layout = QHBoxLayout()
        button_layout = QHBoxLayout()

        input_layout.addWidget(QLabel("Current version:", self))
        self.version_input = QLineEdit(initial_version)
        input_layout.addWidget(self.version_input)

        self.btn_major = QPushButton(self.versions["major"])
        self.btn_major.clicked.connect(lambda: self.select_version(self.versions["major"]))
        button_version_layout.addWidget(self.btn_major)

        self.btn_minor = QPushButton(self.versions["minor"])
        self.btn_minor.clicked.connect(lambda: self.select_version(self.versions["minor"]))
        button_version_layout.addWidget(self.btn_minor)

        self.btn_quick_fix = QPushButton(self.versions["quick_fix"])
        self.btn_quick_fix.clicked.connect(lambda: self.select_version(self.versions["quick_fix"]))
        button_version_layout.addWidget(self.btn_quick_fix)

        main_layout.addLayout(input_layout)
        main_layout.addWidget(QLabel("Quick select new version:", self))
        main_layout.addLayout(button_version_layout)
        main_layout.addLayout(button_layout)

        self.btn_generate = QPushButton("Set")
        self.btn_generate.clicked.connect(self.on_generate)
        button_layout.addWidget(self.btn_generate)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.btn_cancel)

        self.setLayout(main_layout)

    def select_version(self, version):
        VersionUpdater.selected_version = version
        self.close()

    def update_version(self, version_type):
        current_version = self.version_input.text()
        parts = [int(x) for x in current_version.replace("v", "").split(".")]

        if version_type == "major":
            new_version = f"v{parts[0]+1}.0.0"
        elif version_type == "minor":
            new_version = f"v{parts[0]}.{parts[1]+1}.0"
        elif version_type == "quick_fix":
            new_version = f"v{parts[0]}.{parts[1]}.{parts[2]+1}"

        self.version_input.setText(new_version)

    def calculate_versions(self, current_version):
        parts = [int(x) for x in current_version.replace("v", "").split(".")]
        versions = {
            "major": f"v{parts[0]+1}.0.0",
            "minor": f"v{parts[0]}.{parts[1]+1}.0",
            "quick_fix": f"v{parts[0]}.{parts[1]}.{parts[2]+1}",
        }
        return versions

    def on_generate(self):
        VersionUpdater.selected_version = self.version_input.text()
        self.close()

    def on_cancel(self):
        self.close()


def get_current_version(path_to_script):
    version_pattern = r"__version__\s*:\s*str\s*=\s*\"([^\"]+)\""
    try:
        with open(path_to_script, "r") as file:
            contents = file.read()
        match = re.search(version_pattern, contents)
        if match:
            return match.group(1)
    except FileNotFoundError:
        print("File not found. Please check the path.")
    return "v0.0.0"


def get_new_version(path_to_main_script: str) -> str | None:
    app = QApplication(sys.argv)
    set_theme(app, theme="dark")

    current_version = get_current_version(path_to_main_script)

    main_window = VersionUpdater(current_version)
    main_window.show()

    app.exec()

    return VersionUpdater.selected_version


def set_new_version(file_path: str, new_version: str) -> bool:
    version_pattern = re.compile(r'(__version__\s*:\s*str\s*=\s*".*")')
    try:
        with open(file_path, "r") as file:
            contents = file.readlines()
        for i, line in enumerate(contents):
            if "__version__" in line:
                contents[i] = re.sub(version_pattern, f'__version__: str = "{new_version}"', line)
                break
        with open(file_path, "w") as file:
            file.writelines(contents)
        print("Version updated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    return True


def copy_folders_and_clean(folders: list[str], destination: str):
    try:
        for folder in folders:
            dst_path = os.path.join(destination, folder)

            if not os.path.exists(dst_path):
                os.makedirs(dst_path)

            shutil.copytree(folder, dst_path, dirs_exist_ok=True)
            print(f"Copied {folder} into {dst_path}")

        for root, dirs, files in os.walk(destination, topdown=False):
            for name in files:
                if name.endswith(".py"):
                    os.remove(os.path.join(root, name))
                    print(f"Removed file: {os.path.join(root, name)}")
            for name in dirs:
                if name in ["__pycache__", "chat"]:
                    shutil.rmtree(os.path.join(root, name))
                    print(f"Removed directory: {os.path.join(root, name)}")
    except Exception as e:
        print(f"An error occurred while copying folders: {e}")
        return False
    return True


def update_timestamp(file_path: str) -> bool:
    datetime_format = "%Y-%m-%d %H:%M:%S"
    current_datetime = datetime.now().strftime(datetime_format)

    try:
        with open(file_path, "r") as file:
            contents = file.readlines()
        pattern = re.compile(r'(__updated__:\s*str\s*=\s*")[^"]+(")')

        updated_contents = []
        for line in contents:
            new_line = pattern.sub(rf"\g<1>{current_datetime}\g<2>", line)
            updated_contents.append(new_line)

        with open(file_path, "w") as file:
            file.writelines(updated_contents)

        print("Successfully updated the timestamp.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    return True


def compile(spec_file: str) -> bool:
    try:
        print("Running `pyinstaller Invigo.spec`.")
        subprocess.run(["pyinstaller", spec_file], check=True)
        print("Compiling was completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while compiling: {e}")
        return False
    return True


def zip_files(source_dir: str, output_zip: str) -> bool:
    files_to_ignore = ["desktop.ini", "update.exe", "update - Copy.exe"]
    try:
        output_zip_path = f"{output_zip}.zip" if not output_zip.endswith(".zip") else output_zip
        print("Zipping files.")
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, dirnames, filenames in os.walk(source_dir):
                for filename in filenames:
                    print(f"{dirpath}\\{filename}")
                    if filename in files_to_ignore:
                        continue
                    file_path = os.path.join(dirpath, filename)
                    arcname = os.path.relpath(file_path, start=source_dir)
                    zf.write(file_path, arcname)
        print(f"{output_zip} was made successfully.")
    except Exception as e:
        print(f"An error occurred while zipping files: {e}")
        return False
    return True


def copy_file(source: str, destination: str) -> bool:
    try:
        print(f"Uploading {source} file to Pinecone.")
        shutil.copy2(source, destination)
        print(f"{source} uploaded successfully.")
    except Exception as e:
        print(f"An error occurred while uploading {source}: {e}")
        return False
    return True


def update_web_version(version: str) -> bool:
    try:
        print("Updating web version.")
        with open(path_to_web_version, "w") as file:
            file.write(version)
        print(f"{path_to_web_version} successfully updated.")
    except Exception as e:
        print(f"An error occurred while updating {path_to_web_version}: {e}")
        return False
    return True


spec_file_name = "Invigo.spec"
dist_dir = "dist"
output_zip_name = "Invigo"
zip_file = f"{output_zip_name}.zip"
destination_path = r"\\Pinecone\web\Invigo\static"
path_to_main_script = "main.py"
path_to_web_version = r"\\Pinecone\web\Invigo\static\version.txt"


if __name__ == "__main__":
    if new_version := get_new_version(path_to_main_script=path_to_main_script):
        if set_new_version(file_path=path_to_main_script, new_version=new_version):
            if copy_folders_and_clean(folders=["icons", "ui", "utils"], destination="dist"):
                if update_timestamp(file_path=path_to_main_script):
                    if compile(spec_file=spec_file_name):
                        if zip_files(source_dir=dist_dir, output_zip=output_zip_name):
                            if copy_file(
                                source=zip_file,
                                destination=os.path.join(destination_path, zip_file),
                            ):
                                update_web_version(version=new_version)
