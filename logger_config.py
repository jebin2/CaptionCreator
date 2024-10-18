# logger_config.py

import logging
from colorama import Fore, Style, init

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
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a file handler for logging to a file (no colors in the file)
    file_handler = logging.FileHandler('riddle_generation.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Create a console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Add both handlers (console and file) to the root logger
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
