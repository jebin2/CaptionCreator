import logger_config
logging = logger_config.setup_logging()

import json
import get_daily_fen
import stockfish
import common

def fetchData(when=2):
    puzzle_data = get_daily_fen.fetch_daily_puzzles(when)
    try:
        if puzzle_data:
            data = stockfish.process(puzzle_data['fen'], runInHost=common.is_running_in_vm())
            print(f'data: {data}')
            if data['solution']:
                data['fen'] = puzzle_data['fen']
                data['date'] = puzzle_data['date']
                data['whose_turn'] = 'White' if ' w ' in data['fen'] else 'Black'
                
                logging.info(f"\Chess Puzzle: {data}")
                return data

    except Exception as e:
        logging.error(f"Error in chess_puzzle::fetchData : {str(e)}", exc_info=True)

    return None

# Example usage
if __name__ == "__main__":
    # The given position
    fetchData(3)