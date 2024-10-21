from pathlib import Path
import os

def file_exists(file_path):
    return Path(file_path).is_file()

def list_files_recursive(directory):
    # Initialize an empty array to store the file paths
    file_list = []
    
    # Walk through the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get the full path of the file and append to the array
            file_list.append(os.path.join(root, file))
    
    return file_list

def remove_file(file_path):
    try:
        # Check if the file exists
        if os.path.exists(file_path):
            # Remove the file
            os.remove(file_path)
            print(f"{file_path} has been removed successfully.")
        else:
            print(f"{file_path} does not exist.")
    except Exception as e:
        print(f"Error occurred while trying to remove the file: {e}")