import logger_config
logging = logger_config.setup_logging()

import databasecon
import common
import chess_board
import chess_puzzle
import kmcontroller
import json
import convertToVideo

def getCustomInstruction():
    return """Start with "Hello everyone!!, Today's Chess puzzle"
[State board - Board position slowly]
Let's get this going...
[Break down the clues by analyzing and thinking out loud]
[gather insights]
[Arrive at the answer] The answer is [first move]
There you go, [Explanation by playing the answer one by one]
"Thank you for listening"
Rules:
Never acknowledge listener
Direct solving only
Strictly follow sequence exactly
No extra commentary
"""

def getSource(description, answer):
    return f"""{description}
**Answer**
{answer}

"""

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

def getAudioPath(description, answer):
    return kmcontroller.createAudioAndDownload(getCustomInstruction(), getSource(description, answer))

def fetchAndUpdate(when):
    data = chess_puzzle.fetchData(when)
    if data is None:
        return False

    date = data['date']
    white = ' '.join(data['chess_board']['white_position'])
    black = ' '.join(data['chess_board']['black_position'])
    turn = data['whose_turn']
    fen = data['fen']
    description = f"""**Position:**\n
White's position: {white}\n
Black's position: {black}\n

**The Situation:**\n
It's {turn}'s turn.\n
"""
    result = databasecon.execute(f"SELECT * FROM entries WHERE type='chess' AND chess_fen = '{fen}'", type='get')
    if result:
        return False

    answer = format_moves(data['solution'])

    audio_path = getAudioPath(description, answer)

    databasecon.execute("""INSERT into entries (audioPath, title, description, thumbnailText, type, answer, chess_meta, chess_fen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (audio_path, f'How to solve Chess.com daily puzzle : {date}', description, 'Check my video for solution', 'chess', answer, json.dumps(data), fen))

    return True

def start():
    try:
        chess_puzzle = databasecon.execute("SELECT * FROM entries WHERE type='chess' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        if chess_puzzle is None:
            logging.info("No chess puzzle is available")
            is_data_added = False
            when = 0
            while is_data_added is False:
                logging.info(f"Getting chess puzzle today - {when}")
                is_data_added = fetchAndUpdate(when)
                when += 1
                if when > 50:
                    return False
        
        chess_puzzle = databasecon.execute("SELECT * FROM entries WHERE type='chess' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        logging.info(f"Starting to create chess puzzle... {chess_puzzle}")

        if common.file_exists(chess_puzzle[1]) is False:
            audio_path = getAudioPath(chess_puzzle[3], chess_puzzle[5])
            databasecon.execute("""
                    UPDATE entries 
                    SET audioPath = ?
                    WHERE id = ?
                """, (audio_path, chess_puzzle[0]))
            
            chess_puzzle = databasecon.execute("SELECT * FROM entries WHERE id = ? AND type='chess' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", (chess_puzzle[0],), type='get')

        data = json.loads(chess_puzzle[13])
        chess_board.make(data)

        is_success = convertToVideo.process(chess_puzzle[0], chess_puzzle[1])

        databasecon.execute("""
                    UPDATE entries 
                    SET audioPath = 'Done'
                    WHERE id = ?
                """, (chess_puzzle[0],))

    except Exception as e:
        logging.error(f"Error in createChessPuzzle::start : {str(e)}", exc_info=True)
        return False

    return is_success

# if __name__ == "__main__":
#     start()