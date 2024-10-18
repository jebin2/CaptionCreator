# logger_config.py

import logging

def setup_logging():
    # Set up logging configuration
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create a file handler for logging to a file
    file_handler = logging.FileHandler('riddle_generation.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)
    return logging