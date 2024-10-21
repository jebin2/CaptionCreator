import logger_config
logging = logger_config.setup_logging()

import subprocess
import time

def parse_moves(pv_line):
    """Parse principal variation line into moves dictionary"""
    moves_part = pv_line.split(' pv ')[1].strip()
    moves = moves_part.split()
    
    result = {}
    move_count = 1
    
    for i in range(0, len(moves)-1, 2):
        if i + 1 < len(moves):
            result[f"move{move_count}"] = {
                "white": moves[i],
                "black": moves[i+1]
            }
            move_count += 1
    
    # Handle last move if it's a single move
    if len(moves) % 2 == 1:
        result[f"move{move_count}"] = {
            "white": moves[-1],
            "black": None
        }
    
    return result

def convert_to_algebraic_notation(board_visual):
    white = []
    black = []
    
    rows = board_visual.strip().split('\n')[1:-1]  # Skip the top and bottom borders
    
    for rank_index, row in enumerate(rows):
        # Get the pieces from each row and their positions
        cell = 0
        for file_index, char in enumerate(row):
            if char.isalpha():  # Check if the character is a piece
                file = chr(ord('a') + cell-1)  # Convert index to file (a-h)
                if ord(char) < ord('a'):
                    white.append(f"{char}{file}{int(row[-1])}")
                else:
                    black.append(f"{char}{file}{int(row[-1])}")
            if char == '|':
                cell += 1

    return {
        "white_position": white,
        "black_position": black
    }

def stockfish_process(cmd, stockfish_path="/home/jebineinstein/temp/stockfish/stockfish-ubuntu-x86-64-avx2"):
    process = subprocess.Popen(
        [stockfish_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    process.stdin.write(f"{cmd}\n")
    process.stdin.flush()

    board_visual = ''
    moves = ''
    while True:
        line = process.stdout.readline().strip()
        if ' currmovenumber ' in line:
            board_visual = ''
            moves = ''
            break
        if not line:
            continue

        if '+---+' in line or '|   |' in line:
            board_visual += f'{line}\n'
        
        if line.startswith("info depth") and "score mate" in line and "pv" in line:
            moves = line
            print(f'{line}')

        if line.startswith("bestmove"):
            break

    process.terminate()
    process.wait()

    if board_visual and moves:
        board_visual = convert_to_algebraic_notation(board_visual)
        moves = parse_moves(moves)

    logging.info(f"chess_board: {board_visual}")
    logging.info(f"solution: {moves}")

    return board_visual, moves


def process(fen, depth=20, stockfish_path="/home/jebineinstein/temp/stockfish/stockfish-ubuntu-x86-64-avx2"):
    
    board_visual, moves = stockfish_process(f"""position fen {fen}
d
go
""")
    
    return {
        "chess_board": board_visual,
        "solution": moves
    }

if __name__ == "__main__":
    process("4k3/8/4K3/8/8/8/8/8 w - - 0 1")
    # process("q3r1nk/2RQ2n1/1r2Nbp1/1p3P2/1P4P1/Pb6/1B6/K3R3 w - - 0 1")