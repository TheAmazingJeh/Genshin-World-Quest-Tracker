import os, json
import shutil

from tkinter.messagebox import askyesno

def clear_folder(folder, warnAmount=10):
    # Get amount of files and folders in the folder
    num_files = len([f for f in os.listdir(folder)])
    if num_files > warnAmount:
        # Ask for confirmation
        if not askyesno("Warning", f"Are you sure you want to delete {num_files} files?\n\n{folder}"):
            return

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def load_json(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        # Create the file
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump({}, file, indent=4)
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)

def get_image_path(url):
    return f"{url.rsplit(".", maxsplit=1)[0]}.png".split("/")[-1]

def name_to_id(name):
    # Remove special characters and spaces
    for char in [",", "'", "\"", "\\", "/", ":", "*", "?", "!", "<", ">", "|"]:
        name = name.replace(char, "")
    name = name.replace(" ", "_").lower()
    name = name.replace(".", "~")
    return name