import os
import re
import shutil
import subprocess
import zipfile

from datetime import datetime


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
        with open(file_path, 'r') as file:
            contents = file.readlines()
        pattern = re.compile(r'(__updated__:\s*str\s*=\s*")[^"]+(")')

        updated_contents = []
        for line in contents:
            new_line = pattern.sub(rf'\g<1>{current_datetime}\g<2>', line)
            updated_contents.append(new_line)

        with open(file_path, 'w') as file:
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


def update_version(path_to_main_script: str, path_to_web_version: str) -> bool:
    try:
        print("Updating version.")
        with open(path_to_main_script, "r") as file:
            version_pattern = r"__version__\s*:\s*str\s*=\s*\"([^\"]+)\""
            main_script_contents = file.read()
        match = re.search(version_pattern, main_script_contents)
        if match:
            version = match.group(1)
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
    if copy_folders_and_clean(folders=["icons", "ui", "utils"], destination="dist"):
        if update_timestamp(file_path=path_to_main_script):
            if compile(spec_file=spec_file_name):
                if zip_files(source_dir=dist_dir, output_zip=output_zip_name):
                    if copy_file(source=zip_file, destination=os.path.join(destination_path, zip_file)):
                        update_version(path_to_main_script=path_to_main_script, path_to_web_version=path_to_web_version)
