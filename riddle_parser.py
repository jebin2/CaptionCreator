import ollama
import json
import re

def get_ollama_output(transcript, riddle, answer):
    try:
        max_retries = 10
        attempts = 0

        while attempts < max_retries:
            attempts += 1
            response = ollama.chat(model='llama3.2', messages=[
                {
                    'role': 'user',
                    'content': f"""
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
                    
                    3. Riddle End: IMPORTANT - Search for this ONLY in the text that appears AFTER the Riddle Answer text you identified above. Find the last sentence explaining the answer, before any general discussion.

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
                    """
                }
            ])
            
            content = response['message']['content']
            print(f"Check content :: {content}")
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                riddle_data = json.loads(json_match.group())
                if riddle_data["start"] == '' or riddle_data["end"] == '' or riddle_data["answer"] == '':
                    print(f"Retrying due to empty object counter :: {attempts} data :: {riddle_data}")
                else:
                    print(riddle_data)
                    return riddle_data
            else:
                raise ValueError("No valid JSON found in the response")
    
    except Exception as e:
        print(f"Error in get_ollama_output: {e}")
        return None

import re

import re

def calculate_positions(transcript, riddle_data):
    # Normalize the transcript and clean it
    lower_transcript = transcript.lower()
    clean_transcript = re.sub(r'[^a-zA-Z0-9\s]', '', lower_transcript)  # Remove non-alphanumeric except spaces
    clean_transcript = re.sub(r'\s+', ' ', clean_transcript).strip()  # Normalize spaces
    print(f"clean_transcript: {clean_transcript}")
    
    positions = {}
    for key, text in riddle_data.items():
        if text:
            lower_text = text.lower()
            clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', lower_text)  # Clean text similarly
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Normalize spaces
            print(f"clean_text: {clean_text}")

            # Check for exact match first
            match = re.search(re.escape(clean_text), clean_transcript)  # Use escaped cleaned text
            if match:
                positions[key] = match.start()
            else:
                # Split the cleaned text into words for partial matching
                words = clean_text.split()  # Use cleaned text for splitting
                for i in range(len(words), 0, -1):
                    partial_text = r'\s+'.join(re.escape(word) for word in words[:i])  # Create partial regex
                    match = re.search(partial_text, clean_transcript)  # Use cleaned transcript for matching
                    if match:
                        positions[key] = match.start()
                        break
                else:
                    positions[key] = -1  # No match found

        else:
            positions[key] = -1  # If text is empty, assign -1

        # Special handling for the "end" key
        if key == "end" and text.rfind(". ") != -1:
            positions[key] = positions.get(key, -1) + text.rfind(". ") + 2

    return positions


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
                positions = calculate_positions(transcript, riddle_data)
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
