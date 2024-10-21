from logger_config import setup_logging
logging = setup_logging()

import databasecon
import createTextPuzzle

def createContent():
    logging.info("Checking for existing text puzzle to process...")
    
    createTextPuzzle.start()

    createTextPuzzle.start()

if __name__ == "__main__":
    logging.info("Starting...")
    createContent()