import logger_config

import createTextPuzzle
import createChessPuzzle
import create_facts
import databasecon
import gc
import publish_to_yt
import publish_to_x

def createContent(interval=2):
    while True:
        gc.collect()  # Forces garbage collection
        logger_config.info("Starting for text puzzle to process...")

        textEntries = databasecon.execute(f""" 
            SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
            FROM entries
            WHERE (uploadedToYoutube = 0 OR uploadedToYoutube IS NULL)
            AND type = 'text'
        """)
        TEXT_PUZZLE = len(textEntries)

        chessEntries = databasecon.execute(f""" 
            SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
            FROM entries
            WHERE (uploadedToYoutube = 0 OR uploadedToYoutube IS NULL)
            AND type = 'chess'
        """)
        CHESS_PUZZLE = len(chessEntries)

        factsEntries = databasecon.execute(f""" 
            SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
            FROM entries
            WHERE (uploadedToYoutube = 0 OR uploadedToYoutube IS NULL)
            AND type = 'facts'
        """)
        FACTS = len(factsEntries) - 1
        
        logger_config.info(f'{TEXT_PUZZLE}, {2 * CHESS_PUZZLE}, {FACTS}')
        if TEXT_PUZZLE <= 2 * CHESS_PUZZLE or TEXT_PUZZLE <= FACTS:
            is_success = createTextPuzzle.start()
            if is_success:
                logger_config.info("End")
            else:
                logger_config.error("Unable to create text puzzle. please check now...")
                logger_config.error("Unable to create text puzzle. please check now...")
                logger_config.error("Unable to create text puzzle. please check now...")
                logger_config.error("Unable to create text puzzle. please check now...")

            logger_config.info("Starting for chess puzzle to process...")
        
        else:
            logger_config.warning("Skipping Text Puzzle creation as it reached limit...")

        if FACTS <= 2 * CHESS_PUZZLE or FACTS <= TEXT_PUZZLE:
            is_success = create_facts.start()
            if is_success:
                logger_config.info("End")
            else:
                logger_config.error("Unable to create facts. please check now...")
                logger_config.error("Unable to create facts. please check now...")
                logger_config.error("Unable to create facts. please check now...")
                logger_config.error("Unable to create facts. please check now...")
                
        else:
            logger_config.warning("Skipping Chess chess creation as it reached limit...")
        
        if TEXT_PUZZLE > 2 * CHESS_PUZZLE:
            is_success = createChessPuzzle.start()
            if is_success:
                logger_config.info("End")
            else:
                logger_config.error("Unable to create chess puzzle. please check now...")
                logger_config.error("Unable to create chess puzzle. please check now...")
                logger_config.error("Unable to create chess puzzle. please check now...")
                logger_config.error("Unable to create chess puzzle. please check now...")

            logger_config.info(f"Waiting before new content", 10)
        
        else:
            logger_config.warning("Skipping Chess puzzle creation as it reached limit...")

        publish_to_yt.start(0)

        publish_to_x.start(0)

        logger_config.info(f"Waiting before new content iteration", 10)

if __name__ == "__main__":
    logger_config.info("Starting...")
    createContent()