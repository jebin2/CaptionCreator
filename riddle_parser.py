import requests
import ollamaresponseparser
import json
import re
from logger_config import setup_logging

logging = setup_logging()

def get_prompt(riddle, answer, transcript, verify):
    return f"""
        Analyze the following transcription and extract the exact text for these elements:

        Riddle: {riddle}
        Answer: {answer}
        Transcription: {transcript}

        CRITICAL: You must ONLY respond with a JSON object. Do not include ANY other text, explanation, or formatting.
        The response must be in this exact format:

        {{
            "start": "extracted text for riddle start",
            "answer": "extracted text for riddle answer",
            "end": "extracted text for riddle end"
        }}

        Extraction rules:
        1. Riddle Start: The exact text where the actual riddle question or statement begins. Consider the broader context to avoid false positives. Look for first clear indication of a actual riddle about to present/start.
        
        2. Riddle Answer: The exact text where the solution is first mentioned or explained. Look for any clear solution indication.
        
        3. Riddle End: IMPORTANT - Search for this ONLY in the text that appears AFTER the Riddle Answer text you identified above. Find the last sentence explaining the answer, before any general discussion or not necessarily a big discussion.

        Extraction Process:
        1. First identify and extract the start text
        2. Then find and extract the answer text
        3. Finally, look ONLY in the remaining text AFTER the answer text to find the end text
        
        Note: 
        - Be precise in identifying these text excerpts
        - Extract only the specific riddle question or statement, not general discussion
        - Use an empty string for any element you can't find clear text for
        - Maintain chronological order: start text must come before answer text, which must come before end text
        - The end text MUST be found after the answer text in the transcript
        - If you can't find an end text that appears after the answer text, return an empty string for end

        {verify}
    """

def get_ollama_output(transcript, riddle, answer):
    try:
        response = requests.post(ollamaresponseparser.getUrl(), json={
            'model': 'llama3.1',
            'messages': [
                {
                    'role': 'user',
                    'content': get_prompt(riddle, answer, transcript, '')
                }
            ]
        })
        response.raise_for_status()
        
        content = ollamaresponseparser.getParsedData(response.text)
        logging.debug(f"Ollama response content: {content}")

        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            riddle_data = json.loads(json_match.group())
            if riddle_data["start"] == '' or riddle_data["end"] == '' or riddle_data["answer"] == '':
                return None
            else:
                print(riddle_data)
                riddle_data = verify_output(transcript, riddle, answer, riddle_data)
                print(riddle_data)
                return riddle_data
        else:
            raise ValueError("No valid JSON found in the response")
    
    except Exception as e:
        print(f"Error in get_ollama_output: {e}")
        return None

def verify_output(transcript, riddle, answer, riddle_data):
    try:
        response = requests.post(ollamaresponseparser.getUrl(), json={
            'model': 'llama3.1',
            'messages': [
                {
                    'role': 'user',
                    'content': get_prompt(riddle, answer, transcript, """
                    Below is the answer given by you previously for ther above prompt.

                    ansmwer: {riddle_data}
                    
                    Please review the following answer for accuracy and clarity:
                    Is this answer correct? return the same
                    If the answer needs improvement, please make the necessary changes and provide the revised answer follow the answer format always.
                """)
                }
            ]
        })
        response.raise_for_status()
        
        content = ollamaresponseparser.getParsedData(response.text)
        logging.debug(f"Ollama response content: {content}")

        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            new_riddle_data = json.loads(json_match.group())
            if new_riddle_data["start"] == '' or new_riddle_data["end"] == '' or new_riddle_data["answer"] == '':
                return riddle_data
            else:
                return new_riddle_data
    
    except Exception as e:
        print(f"Error in get_ollama_output: {e}")
        return riddle_data
    

def calculate_positions(transcript, test_search, _type):
    def get_clean_to_original_mapping(text):
        cleaned_text = ''
        position_map = {}
        cleaned_pos = 0
        
        for orig_pos, char in enumerate(text):
            if char.isalnum() or char.isspace():
                cleaned_text += char
                position_map[cleaned_pos] = orig_pos
                cleaned_pos += 1
                
        return cleaned_text, position_map

    def incremental_search(search_text, target_text):
        if not search_text:
            return -1
            
        words = search_text.split()
        current_position = -1
        
        # First try exact match
        for i in range(len(words)):
            partial_text = ' '.join(words[:i+1])
            print(f"{partial_text}")
            match = target_text.find(partial_text)
            
            # Try case-insensitive match
            if match == -1:
                match = target_text.lower().find(partial_text.lower())
            
            # If still no match, try with cleaned text while maintaining original position
            if match == -1:
                cleaned_target, position_map = get_clean_to_original_mapping(target_text)
                cleaned_search = ''.join(c for c in partial_text.lower() if c.isalnum() or c.isspace())
                match = cleaned_target.lower().find(cleaned_search)
                
                # Map cleaned position back to original position
                if match != -1 and match in position_map:
                    match = position_map[match]
            
            if match != -1:
                current_position = match
            else:
                break
                
        return current_position

    positions = {}
    
    # Handle empty text case
    if not test_search:  
        positions["index"] = -1
    else:
        position = incremental_search(test_search, transcript)
        positions["index"] = position
        
        # Special handling for the "end" type
        if _type == "end" and position != -1:
            last_period_pos = test_search.find('. ')
            if last_period_pos != -1:
                positions["index"] = position + last_period_pos + 2

    return positions["index"]


def insert_text(original_string, text_to_insert, index):
    if index == -1:
        return original_string
    index = max(0, min(int(index), len(original_string)))
    return original_string[:index] + text_to_insert + original_string[index:]

def add_markers_to_transcript(transcript, positions):
    marked_transcript = transcript
    markers = [
        ("start", "--#start#--"),
        ("answer", "--#answer#--"),
        ("end", "--#end#--")
    ]
    
    sorted_markers = sorted(
        [(key, marker) for key, marker in markers if positions.get(key, -1) != -1],
        key=lambda x: positions[x[0]],
        reverse=True
    )

    for key, marker in sorted_markers:
        position = positions[key]
        marked_transcript = insert_text(marked_transcript, marker, position)

    return marked_transcript

def validate_riddle_positions(transcript, positions):
    valid_positions = all(pos != -1 for pos in positions.values())
    correct_order = positions['start'] < positions['answer'] < positions['end'] if valid_positions else False

    if not valid_positions:
        print("Warning: One or more riddle positions could not be identified.")
    elif not correct_order:
        print("Warning: Riddle positions are not in the correct order.")

    for key, position in positions.items():
        if position != -1:
            context = transcript[max(0, position-50):min(len(transcript), position+50)]
            print(f"{key.capitalize()} context: ...{context}...")

    return valid_positions and correct_order

def process_convo_text(transcript, riddle, answer):
    max_retries = 100
    attempts = 0

    while attempts < max_retries:
        try:
            riddle_data = get_ollama_output(transcript, riddle, answer)
            if riddle_data:
                positions = {}
                for key, text in riddle_data.items():
                    positions[key] = calculate_positions(transcript, text, key)
                    print(f"{positions}")
                if validate_riddle_positions(transcript, positions):
                    return add_markers_to_transcript(transcript, positions)
                else:
                    print(f"Attempt {attempts + 1}: Invalid positions, retrying...")
            else:
                print("Failed to process the transcript accurately.")
            
            attempts += 1

        except Exception as e:
            print(f"An error occurred in process_convo_text: {e}")
            return None

    print("Max retries reached. Returning original transcript.")
    return None
