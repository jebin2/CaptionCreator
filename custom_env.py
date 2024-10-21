import common

isVM = common.is_running_in_vm()
base_path = '/media/sf_CaptionCreator' if isVM else '/home/jebineinstein/git/CaptionCreator'
DATABASE_PATH = f'{base_path}/ContentData/entries.db'
AUDIO_PATH = f'{base_path}/audio'
VIDEO_PATH = f'{base_path}/video'
CHESS_PATH = f'{base_path}/chess'
CHESS_BOARD_SVG = f'{CHESS_PATH}/chess_board.svg'
CHESS_BOARD_JPG = f'{CHESS_PATH}/chess_board.jpg'
CHESS_BOARD_WITH_PUZZLE_SVG = f'{CHESS_PATH}/chess_board_with_puzzle.svg'
CHESS_BOARD_WITH_PUZZLE_JPG = f'{CHESS_PATH}/chess_board_with_puzzle.jpg'
CHESS_MOVES_PATH = f'{CHESS_PATH}/moves'
FPS=24