import logger_config
logging = logger_config.setup_logging()

import createTextPuzzle
import createChessPuzzle

def createContent(interval=10):
    while True:
        logging.info("Starting for text puzzle to process...")

        is_success = createTextPuzzle.start()
        if is_success:
            logging.info("End")
        else:
            logging.error("Unable to create text puzzle. please check now...")
            logging.error("Unable to create text puzzle. please check now...")
            logging.error("Unable to create text puzzle. please check now...")
            logging.error("Unable to create text puzzle. please check now...")

        logging.info("Starting for text puzzle to process...")
        
        is_success = createChessPuzzle.start()
        if is_success:
            logging.info("End")
        else:
            logging.error("Unable to create chess puzzle. please check now...")
            logging.error("Unable to create chess puzzle. please check now...")
            logging.error("Unable to create chess puzzle. please check now...")
            logging.error("Unable to create chess puzzle. please check now...")

        logger_config.wait_with_logs(interval, "for next content to create...")        

if __name__ == "__main__":
    logging.info("Starting...")
    createContent()