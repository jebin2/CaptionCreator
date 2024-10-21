from logger_config import setup_logging
logging = setup_logging()

import os
from pathlib import Path
import logging
from typing import List, Tuple, Optional
from lxml import etree
import chess_puzzle
import common
import time
import svgtojpg
import custom_env

# Constants
SQUARE_SIZE = 135
TOTAL_SIZE = 945
DESIRED_WIDTH = 1920  # Set your desired width for YouTube video
DESIRED_HEIGHT = 1080  # Set your desired height for YouTube video

# Piece mappings
PIECE_TO_ID = {
    'k': "#king",
    'q': "#queen",
    'b': "#bishop",
    'n': "#knight",
    'r': '#rook',
    'p': '#pawn'
}

ID_TO_PIECE = {v: k for k, v in PIECE_TO_ID.items()}

FILE_TO_NUM = {'a': "0", 'b': "1", 'c': "2", 'd': "3", 
               'e': '4', 'f': '5', 'g': '6', 'h': '7'}
RANK_TO_NUM = {str(i): str(i-1) for i in range(1, 9)}

def get_available_move_for_chess_pieces(isWhiteMove, whitePiecesNotation, blackPiecesNotation):
    return f"""Given a chess position with the following pieces:

White pieces: {whitePiecesNotation}
Black pieces: {blackPiecesNotation}
Current turn: {'White' if isWhiteMove else 'Black'} turn

Generate a JSON object where:
- Each key is a piece's current position in algebraic notation (e.g., "e2")
- Each value is an array of all legal moves for that piece in algebraic notation (e.g., ["e3", "e4"])

Example format:
{{
    "e2": ["e3", "e4"],
    "g1": ["f3", "h3"],
    "b1": ["c3", "a3"]
}}

Rules:
1. Only include pieces that have at least one legal move
2. Use standard algebraic notation (a1 to h8)
3. Include castling moves if legal (represented as king moves: e1g1 for white kingside castle)
4. Consider all chess rules including:
   - Check and checkmate
   - Pinned pieces
   - En passant when legal
   - Pieces blocking movement paths

Respond ONLY with the JSON object, no additional text or explanations."""

def convert_chess_notation_to_pixels(file: str, rank: str) -> Tuple[int, int]:
    """Convert chess notation (e.g., 'e4') to pixel coordinates."""
    try:
        x = int(FILE_TO_NUM[file]) * SQUARE_SIZE
        y = TOTAL_SIZE - (int(RANK_TO_NUM[rank]) * SQUARE_SIZE)
        return x, y
    except KeyError as e:
        logging.error(f"Invalid chess notation: {file}{rank}")
        raise ValueError(f"Invalid chess notation: {file}{rank}") from e

def get_piece_details_from_notation(notation: str) -> Tuple[str, int, int]:
    """Extract piece ID and coordinates from chess notation."""
    piece, file, rank = notation[0], notation[1], notation[2]
    piece_id = PIECE_TO_ID.get(piece.lower())
    if not piece_id:
        raise ValueError(f"Invalid piece notation: {piece}")
    x, y = convert_chess_notation_to_pixels(file, rank)
    return piece_id, x, y

def get_piece_from_coordinates(tree: etree._ElementTree, is_white: bool, notation: str) -> Optional[str]:
    root = tree.getroot()
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    piece_group = root.find(
        f".//svg:g[@id='{'white' if is_white else 'black'}pieces']",
        namespaces
    )
    
    if piece_group is not None:
        for child in piece_group:
            if notation in child.get('_id', ''):
                return ID_TO_PIECE.get(child.get('href'))

    return None

def empty_element(element):
    for child in list(element):
        element.remove(child)

def remove_element_by_id(element, idVal):
    for child in list(element):
        if idVal in child.get('_id', ''):
            print(f"removed {idVal}")
            element.remove(child)

def get_modified_content(isCreate, tree, whiteNotationSeparateBySpace, blackNotationSeparateBySpace, removeNotation=None, point=None, removeDestPiece=False):
    logging.info(f"White:: {whiteNotationSeparateBySpace}")
    logging.info(f"Black:: {blackNotationSeparateBySpace}")
    logging.info(f"Remove:: {removeNotation}")
    root = tree.getroot()

    for type in ['white', 'black']:
        if type == 'white' and whiteNotationSeparateBySpace is None:  # Fixed: Proper condition checking
            continue
        if type == 'black' and blackNotationSeparateBySpace is None:  # Fixed: Proper condition checking
            continue

        namespaces = {'svg': 'http://www.w3.org/2000/svg'}
        piecesElement = root.find(".//svg:g[@id='whitepieces']", namespaces) if type == 'white' else root.find(".//svg:g[@id='blackpieces']", namespaces)

        if piecesElement is not None:
            if isCreate:
                empty_element(piecesElement)
            
            if removeNotation is not None:
                for notation in removeNotation.split(" "):
                    if whiteNotationSeparateBySpace is not None or removeDestPiece:
                        piecesElement = root.find(".//svg:g[@id='whitepieces']", namespaces)
                        if piecesElement is not None:
                            remove_element_by_id(piecesElement, notation)
                    if blackNotationSeparateBySpace is not None or removeDestPiece:
                        piecesElement = root.find(".//svg:g[@id='blackpieces']", namespaces)
                        if piecesElement is not None:
                            remove_element_by_id(piecesElement, notation)

            piecesElement = root.find(".//svg:g[@id='whitepieces']", namespaces) if type == 'white' else root.find(".//svg:g[@id='blackpieces']", namespaces)

            notations = whiteNotationSeparateBySpace.split(" ") if type == 'white' else blackNotationSeparateBySpace.split(" ")
            for notation in notations:
                pieceId, x, y = get_piece_details_from_notation(notation)
                if point is not None:
                    x, y = point
                new_use_element = etree.Element("use", 
                    attrib={
                        'href': pieceId,
                        'x': str(x),
                        'y': str(y),
                        'width': str(SQUARE_SIZE),
                        'height': str(SQUARE_SIZE),
                        '_id': notation
                    })
                new_use_element.tail = "\n"
                piecesElement.append(new_use_element)
    
    return tree

def create_svg(output_file, chess_board, whiteNotationSeparateBySpace, blackNotationSeparateBySpace):
    try:
        logging.info(f"File Path:: {chess_board}")
        tree = get_modified_content(True, etree.parse(chess_board), whiteNotationSeparateBySpace, blackNotationSeparateBySpace)
        tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        svgtojpg.convert_svg_to_jpg(str(output_file), str(output_file).replace(".svg", ".jpg"), DESIRED_WIDTH, DESIRED_HEIGHT)
    except Exception as e:
        logging.error(f"create_svg : {str(e)}", exc_info=True)
        return None
    return output_file

def pointsToMove(fromX, fromY, toX, toY, noOfP):
    xMean = (toX - fromX) / (noOfP - 1)
    yMean = (toY - fromY) / (noOfP - 1)

    # Generate points
    points = []
    for i in range(noOfP):
        x = fromX + xMean * i
        y = fromY + yMean * i
        points.append((round(x), round(y)))

    logging.info(f"Moveing points: {points}")
    return points

def update_n_create_svg(base_path, isWhiteMove, file_name, notationFromTo, order):
    try:
        logging.info(f"Move by:: {'White' if isWhiteMove else 'Black'}")
        logging.info(f"File :: {file_name}")
        logging.info(f"Notation:: {notationFromTo}")
        fromX, fromY = convert_chess_notation_to_pixels(notationFromTo[0], notationFromTo[1])
        toX, toY = convert_chess_notation_to_pixels(notationFromTo[2], notationFromTo[3])
        logging.info(f"Move from ({fromX}, {fromY}) - To ({toX}, {toY})")

        points = pointsToMove(fromX, fromY, toX, toY, custom_env.FPS)
        count = 0
        removeNotation = notationFromTo[:2] + " " + notationFromTo[2:]
        tree = etree.parse(file_name)
        piece = get_piece_from_coordinates(tree, isWhiteMove, notationFromTo[:2])
        addNotation = f'{piece}{notationFromTo[2:]}'  # Fixed: Variable name typo
        output_svg_file = None
        for point in points:
            output_svg_file = f'{base_path}/new_chess_board-update-{order}-{count}.svg'  # Fixed: Simplified file naming
            tree = etree.parse(file_name)
            tree = get_modified_content(
                False, 
                tree,
                addNotation if isWhiteMove else None,
                addNotation if not isWhiteMove else None,  # Fixed: Logic error
                removeNotation=removeNotation,
                point=point,
                removeDestPiece=(count + 1 == custom_env.FPS)
            )
            tree.write(output_svg_file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            svgtojpg.convert_svg_to_jpg(output_svg_file, str(output_svg_file).replace(".svg", ".jpg"), DESIRED_WIDTH, DESIRED_HEIGHT)
            count += 1

        return output_svg_file

    except Exception as e:
        logging.error(f"update_svg : {str(e)}", exc_info=True)
        return None

def make(data) -> Optional[str]:
    try:

        # data = {'chess_board': {'white_position': ['Qe6', 'Nd5', 'Pg4', 'Pa3', 'Pf3', 'Bf1', 'Kg1'], 'black_position': ['bb8', 're8', 'rh8', 'pb7', 'kh7', 'pa6', 'pc5', 'pd4', 'ph3', 'qd1']}, 'solution': {'move1': {'white': 'e6f7', 'black': 'h7h6'}, 'move2': {'white': 'g4g5', 'black': 'h6g5'}, 'move3': {'white': 'f7g7', 'black': 'g5h5'}, 'move4': {'white': 'd5f6', 'black': 'h5h4'}, 'move5': {'white': 'g7g4', 'black': None}}, 'fen': '1b2r2r/1p5k/p3Q3/2pN4/3p2P1/P4P1p/8/3q1BK1 w - - 0 1', 'date': '2024-10-19', 'whose_turn': 'White'}

        
        white_pieces = data["chess_board"]["white_position"]
        black_pieces = data["chess_board"]["black_position"]

        turn = data['whose_turn']
        
        # Create initial board
        chess_board = create_svg(
            custom_env.CHESS_BOARD_WITH_PUZZLE_SVG,
            custom_env.CHESS_BOARD_SVG,
            ' '.join(white_pieces),
            ' '.join(black_pieces)
        )
        
        # Process moves
        moves_dir = custom_env.CHESS_MOVES_PATH
        common.remove_directory(moves_dir)
        time.sleep(1)
        common.create_directory(moves_dir)
        order = 0

        for move_num, move in enumerate(data["solution"].values()):
            # Process white move
            if turn == 'White':
                if move["white"]:
                    order = order + 1
                    chess_board = update_n_create_svg(
                        moves_dir,
                        True,  # is_white_move
                        chess_board,
                        move["white"],
                        order
                    )
                
                if move["black"]:
                    order = order + 1
                    chess_board = update_n_create_svg(
                        moves_dir,
                        False,  # is_white_move
                        chess_board,
                        move["black"],
                        order
                    )
            
            else:
                if move["black"]:
                    order = order + 1
                    chess_board = update_n_create_svg(
                        moves_dir,
                        False,  # is_white_move
                        chess_board,
                        move["black"],
                        order
                    )

                if move["white"]:
                    order = order + 1
                    chess_board = update_n_create_svg(
                        moves_dir,
                        True,  # is_white_move
                        chess_board,
                        move["white"],
                        order
                    )
        
        return custom_env.base_path
        
    except Exception as e:
        logging.error(f"Error creating chess board: {str(e)}", exc_info=True)
        return None

# if __name__ == "__main__":
#     make(chess_puzzle.fetchData())