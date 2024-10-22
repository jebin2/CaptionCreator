from pathlib import Path
import os
import subprocess
import shutil
import string
import random
from datetime import datetime, timedelta

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

def is_running_in_vm():
    try:
        output = subprocess.check_output(['whoami']).decode().strip()
        # Check for common hypervisor names
        if "vboxuser" in output:
            return True
    except Exception:
        pass
    
    return False

def remove_directory(directory_path):
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            print(f'Directory Deleted at: {directory_path}')
    except Exception as e:
        print(f'An error occurred: {e}')

def create_directory(directory_path):
    try:
        # Create the directory
        os.makedirs(directory_path, exist_ok=True)  # exist_ok=True avoids error if the dir already exists
        print(f'Directory created at: {directory_path}')
    except Exception as e:
        print(f'An error occurred: {e}')

def generate_random_string(length=6):
    # Define the characters to choose from (uppercase, lowercase, digits)
    characters = string.ascii_letters
    # Generate a random string
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def get_date(when=0):
    today = datetime.now()
    sub_day = today - timedelta(days=when)

    sub_day_str = sub_day.strftime('%Y-%m-%d')    
    return sub_day_str