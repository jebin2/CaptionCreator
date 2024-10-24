import logger_config
import databasecon
import chess_puzzle
import json
import convertToVideo
import create_riddles
import common

START_WITH = 'Hello everyone'

def format_moves(moves):
    formatted_moves = "The answer is "
    for move in moves.values():
        white_move = move["white"]
        black_move = move["black"]
        if white_move:
            # formatted_moves.append(f"White: {white_move[:2]}-{white_move[2:]}")
            formatted_moves += f"White: {white_move[:2]}-{white_move[2:]}"
            break
        else:
            formatted_moves.append(f"White: null")
        if black_move:
            # formatted_moves.append(f"Black: {black_move[:2]}-{black_move[2:]}")
            formatted_moves += f"Black: {black_move[:2]}-{black_move[2:]}"
            break
        else:
            formatted_moves.append(f"Black: null")
    # Join all moves with a comma and return
    return formatted_moves

def start():
    try:
        text_puzzle = databasecon.execute("SELECT * FROM entries WHERE type ='text' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        if text_puzzle is None:
            logger_config.info("No text puzzle is available")
            is_data_added = False
            when = 0
            while is_data_added is False:
                logger_config.info(f"Getting text from llama...")
                is_data_added = create_riddles.start()
                when += 1
                if when > 50:
                    return False
        
        text_puzzle = databasecon.execute("SELECT * FROM entries WHERE type = 'text' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        logger_config.info(f"Starting to create text puzzle... {text_puzzle}")

        if common.file_exists(text_puzzle[1]) is False:
            create_riddles.start({
                'id': text_puzzle[0],
                'riddle': text_puzzle[3],
                'answer': text_puzzle[5],
            })
            text_puzzle = databasecon.execute("SELECT * FROM entries WHERE id = ? AND type = 'text' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", (text_puzzle[0],),  type='get')
        
        is_success = convertToVideo.process(text_puzzle[0], text_puzzle[1], START_WITH)
        
        if is_success:
            databasecon.execute("""
                    UPDATE entries 
                    SET audioPath = 'Done'
                    WHERE id = ?
                """, (text_puzzle[0],))
        else:
            databasecon.execute("""
                UPDATE entries 
                    SET audioPath = 'Failed',
                    generatedVideoPath = '',
                    generatedThumbnailPath = ''
                WHERE id = ?
            """, (text_puzzle[0],))

    except Exception as e:
        logger_config.error(f"Error in createChessPuzzle::start : {str(e)}")
        return False

    return is_success

# if __name__ == "__main__":
#     start()