import logging
from colorama import Fore, Style, init
import time

def setup_logging():
    # Initialize Colorama for Windows compatibility
    init(autoreset=True)

    # Custom Formatter with Colors for console output
    class CustomFormatter(logging.Formatter):
        # Define colors for each log level
        LOG_COLORS = {
            logging.INFO: Fore.GREEN + Style.BRIGHT,
            logging.ERROR: Fore.RED + Style.BRIGHT,
            logging.WARNING: Fore.YELLOW + Style.BRIGHT,
            logging.DEBUG: Fore.BLUE + Style.BRIGHT,
            logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
        }

        def format(self, record):
            log_color = self.LOG_COLORS.get(record.levelno, Fore.WHITE)
            message = super().format(record)
            return log_color + message + Style.RESET_ALL

    # Set up logging configuration
    logger = logging.getLogger()

    # Remove any existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Add the console handler to the logger
    logger.addHandler(console_handler)

    # Set the logger level
    logger.setLevel(logging.INFO)

    return logger

def wait_with_logs(seconds, text=''):
    localog = setup_logging()
    try:
        localog.info(f"Waiting {text} for {seconds} seconds.")
        for i in range(seconds, 0, -1):
            localog.info(f"Wait time remaining: {i} seconds.")
            time.sleep(1)
        localog.info("Wait period finished.")
    except Exception as e:
        localog.error(f"Error during wait: {str(e)}", exc_info=True)

# Usage example
# if __name__ == "__main__":
#     logger = setup_logging()
#     logger.info("This is an info message.")
#     logger.warning("This is a warning message.")
#     logger.error("This is an error message.")
#     logger.debug("This is a debug message.")
#     logger.critical("This is a critical message.")
