import os
import shutil
import zipfile


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


dist_dir = "dist"
output_zip_name = "Invigo"
zip_file = f"{output_zip_name}.zip"
destination_path = r"\\Pinecone\web\Invigo\static"


if __name__ == "__main__":
    if copy_folders_and_clean(folders=["icons", "ui", "utils"], destination="dist"):
        if zip_files(source_dir=dist_dir, output_zip=output_zip_name):
            copy_file(source=zip_file, destination=os.path.join(destination_path, zip_file))
