import requests
import json
from datetime import datetime, timedelta
import re

def get_date_range(when=2):
    today = datetime.now()
    yesterday = today - timedelta(days=when)
    
    # Format dates as YYYY-MM-DD
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    return yesterday_str, today_str

def fetch_daily_puzzles(when=2):
    start_date, end_date = get_date_range(when)
    print(f"Fetching puzzles from {start_date} to {end_date}")
    
    url = f"https://www.chess.com/callback/puzzles/daily?start={start_date}&end={end_date}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.chess.com/puzzles/daily'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        puzzles = response.json()
        
        fen_pattern = r'\[FEN "(.*?)"\]'
        fen = None
        print(puzzles)
        for puzzle in puzzles:
            pgn_text = puzzle['pgn']
            match = re.search(fen_pattern, pgn_text)
            fen = None
            if match:
                fen = match.group(1)
                print(f"1) FRN: {fen}")
            
            puzzle_data = {
                'date': puzzle.get('date', ''),
                'fen': fen
            }
            break
        
        print(f"puzzle_data : {puzzle_data}")
        return puzzle_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching puzzles: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    
    return None

def print_puzzle_data(puzzles):
    for puzzle in puzzles:
        print("\n" + "="*50)
        print(f"Date: {puzzle['date']}")
        print(f"Title: {puzzle['title']}")
        print(f"Rating: {puzzle['rating']}")
        print(f"FEN: {puzzle['fen']}")
        print(f"URL: {puzzle['url']}")

# if __name__ == "__main__":
#     today_fen = fetch_daily_puzzles()
#     print(f"today_fen: {today_fen}")
#     if puzzles:
#         print_puzzle_data(puzzles)
        
#         # Print just the FENs
#         print("\nJust the FENs:")
#         for puzzle in puzzles:
#             print(f"{puzzle['date']}: {puzzle['fen']}")
#     else:
#         print("No puzzles found or error occurred.")