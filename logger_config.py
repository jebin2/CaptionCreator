import logging
import time

def setup_logging():
    # Set up logging configuration
    logger = logging.getLogger()

    # Remove any existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Set formatter without styling
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Add the console handler to the logger
    logger.addHandler(console_handler)

    # Set the logger level
    logger.setLevel(logging.INFO)

    return logger

localog = setup_logging()

def wait_with_logs(seconds, text=''):
    try:
        localog.info(f"Waiting {text} for {seconds} seconds.")
        for i in range(seconds, 0, -1):
            localog.info(f"Wait time remaining: {i} seconds.")
            time.sleep(0.5)  # Reduced sleep to make it faster
        localog.info("Wait period finished.")
    except Exception as e:
        localog.error(f"Error during wait: {str(e)}", exc_info=True)

# Usage example
# if __name__ == "__main__":
#     wait_with_logs(5, "example")
