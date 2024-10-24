import time
import glob
import os
import common
import logger_config

is_pygui_available = True
try:
    import pyautogui
    import cv2
    import numpy as np
except KeyError as e:
    is_pygui_available = False


directory = '/media/sf_CaptionCreator/audio/'

def find_and_click(icon_path, wait_before_click=2, wait_time=2):
    logger_config.info(f"Attempting to find and click: {icon_path}")
    
    # Load the screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    
    # Load the screenshot and the template image of the icon to find
    screenshot = cv2.imread('screenshot.png')
    template = cv2.imread(icon_path)

    # Check if images are loaded
    if screenshot is None:
        logger_config.info("Error: Screenshot could not be loaded.")
        return False
    if template is None:
        logger_config.info(f"Error: Template image {icon_path} could not be loaded.")
        return False

    # Convert both images to grayscale
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # Get the width and height of the template
    h, w = template_gray.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8  # Threshold for detection
    loc = np.where(result >= threshold)

    # Draw rectangles around matched locations and click on the first match
    for pt in zip(*loc[::-1]):  # Switch columns and rows
        click_position = (pt[0] + w // 2, pt[1] + h // 2)  # Center position
        if wait_before_click != 0:
            pyautogui.moveTo(click_position)
        time.sleep(wait_before_click)
        pyautogui.click(click_position)  # Click at the position
        logger_config.info(f"Clicked at: {click_position}")
        time.sleep(wait_time)
        return True  # Exit after clicking the first match

    logger_config.info(f"Icon not found: {icon_path}")
    return False  # Return False if no icon was found

def is_generating_output(delete=False):
    logger_config.info("Checking if output is generating...")
    while True:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        screenshot = cv2.imread('screenshot.png')
        generating_icon = cv2.imread('icon/generating_output.png', cv2.IMREAD_GRAYSCALE)

        if generating_icon is None:
            logger_config.info("Generating output icon not found, proceeding...")
            if delete:
                delete_audio()
            return

        # Convert to grayscale and perform matching
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(screenshot_gray, generating_icon, cv2.TM_CCOEFF_NORMED)

        if np.max(result) < 0.8:
            logger_config.info("Generating output icon not found, proceeding...")
            if delete:
                delete_audio()
            break

        time.sleep(1)  # Check again after 1 second

def delete_audio():
    logger_config.info("Deleting audio...")
    find_and_click('icon/hamburger_icon.png')
    find_and_click('icon/delete_option.png')
    time.sleep(5)
    find_and_click('icon/audio_delete_button.png', wait_time=5)
    time.sleep(5)
    logger_config.info("Audio deleted.")

def delete_source():
    logger_config.info("Attempting to delete source...")
    while True:
        # Capture a new screenshot each time
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        screenshot = cv2.imread('screenshot.png', cv2.IMREAD_GRAYSCALE)
        
        # Load the source file icon template
        source_file_icon = cv2.imread('icon/source_file_icon.png', cv2.IMREAD_GRAYSCALE)

        # Check if the source file icon image is loaded correctly
        if source_file_icon is None:
            logger_config.info("Source file icon template not found. Exiting delete_source.")
            return

        # Perform template matching
        result = cv2.matchTemplate(screenshot, source_file_icon, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(result >= threshold)

        # If no match is found, exit the loop
        if len(loc[0]) == 0:
            logger_config.info("Source file icon not found in screenshot. Exiting delete_source.")
            return
        
        # If a match is found, proceed with clicks
        find_and_click('icon/source_file_icon.png')
        find_and_click('icon/remove_source_file_option.png')
        find_and_click('icon/source_alert_delete_button.png', wait_time=5)
        time.sleep(5)
        logger_config.info("Source file deleted successfully.")

def createAudioAndDownload(custom_instruction, source):
    try:
        if not is_pygui_available:
            logger_config.info("Error: DISPLAY environment variable is not set. Exiting program.")
            return None

        logger_config.info(F"Custom Instruction: {custom_instruction}")
        logger_config.info(F"Source: {source}")
        # Allow some time to switch to the desired window
        logger_config.info("Waiting for 5 seconds before starting...")
        time.sleep(5)

        # Start the deletion process for the source file
        delete_source()

        # Find and click the specified icons in sequence
        if not find_and_click('icon/add_icon.png'):
            logger_config.info("Failed to find the add icon. Exiting...")
            return None
        if not find_and_click('icon/copy_text_button.png'):
            logger_config.info("Failed to find the copy text button. Exiting...")
            return None
        if not find_and_click('icon/paste_input_box.png'):
            logger_config.info("Failed to find the paste input box. Exiting...")
            return None

        # Paste text (you can replace 'your text' with the actual text you want to paste)
        logger_config.info("Pasting text into the input box...")
        pyautogui.write(source, interval=0.1)  # Simulate typing
        time.sleep(5)

        if not find_and_click('icon/paste_input_box_insert_button.png', wait_time=5):
            logger_config.info("Failed to find the paste input box insert button. Exiting...")
            return None

        is_generating_output(True)

        if not find_and_click('icon/customise_button.png'):
            logger_config.info("Failed to find the customise button. Exiting...")
            return None

        # Paste text again if needed
        logger_config.info("Pasting text into the customise field...")
        pyautogui.write(custom_instruction, interval=0.1)
        time.sleep(2)

        if not find_and_click('icon/customize_generate_icon.png'):
            logger_config.info("Failed to find the customize generate icon. Exiting...")
            return None

        is_generating_output()

        if not find_and_click('icon/hamburger_icon.png'):
            logger_config.info("Failed to find the hamburger icon. Exiting...")
            return None

        if not find_and_click('icon/download_option.png', wait_time=5):
            logger_config.info("Failed to find the download option. Exiting...")
            return None
        
        logger_config.info("Process completed successfully.")
        # Ensure the directory is not empty
        # Get the list of all files in the directory
        list_of_files = glob.glob(os.path.join(directory, '*'))  # Get all file paths
        if list_of_files:
            latest_file = max(list_of_files, key=os.path.getctime)

            file_directory = os.path.dirname(latest_file)
            new_file_name = os.path.join(file_directory, f'{common.generate_random_string()}.wav')
            
            os.rename(latest_file, new_file_name)
            print(f"The latest created file is: {new_file_name}")
            
            return new_file_name
    
    except Exception as e:
        logger_config.error(f"Error updating database: {str(e)}")

    return None