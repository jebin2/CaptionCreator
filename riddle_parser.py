import ollama
import json
import re

def get_ollama_output(transcript, riddle):
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'user',
                'content': f"""
                Analyze the following transcription and extract the exact text for these elements:

                Riddle: {riddle}
                Transcription: {transcript}

                1. Riddle Start: The exact text where the actual riddle question or statement begins. Consider the broader context to avoid false positives. Look for first clear indication of a actual riddle about to present/start.

                2. Riddle Answer: The exact text where the solution is first mentioned or explained. Look for any clear solution indication.

                3. Riddle End: The exact text of the last word of that sentences explaining the answer, before any general discussion or reflection. Focus on the conclusion of the explanation, not necessarily the end of all riddle-related talk.

                Provide the response as a JSON object with the extracted text:

                {{
                    "start": "extracted text for riddle start",
                    "answer": "extracted text for riddle answer",
                    "end": "extracted text for riddle end"
                }}

                Note: 
                - Be precise in identifying these text excerpts. 
                - Extract only the specific riddle question or statement, not general discussion.
                - Use an empty string for any element you can't find clear text for.
                - Ensure the excerpts are in the correct order as they appear in the transcript.
                - For the end, focus on the last explanatory sentence, not necessarily the end of all riddle discussion.
                """
            }
        ])
        
        content = response['message']['content']
        json_match = re.search(r'\{[^{}]*\}', content)
        if json_match:
            riddle_data = json.loads(json_match.group())
            print(riddle_data)
            return riddle_data
        else:
            raise ValueError("No valid JSON found in the response")
    
    except Exception as e:
        print(f"Error in get_ollama_output: {e}")
        return None

def calculate_positions(transcript, riddle_data):
    positions = {}
    for key, text in riddle_data.items():
        if text:
            # Convert both the transcript and the search text to lowercase
            lower_transcript = transcript.lower()
            lower_text = text.lower()
            
            # Use regex to find the position, allowing for some flexibility
            match = re.search(re.escape(lower_text).replace(r'\ ', r'\s+'), lower_transcript)
            if match:
                positions[key] = match.start()
            else:
                # If exact match fails, try finding a close match
                words = lower_text.split()
                for i in range(len(words), 0, -1):
                    partial_text = r'\s+'.join(re.escape(word) for word in words[:i])
                    match = re.search(partial_text, lower_transcript)
                    if match:
                        positions[key] = match.start()
                        break
                else:
                    positions[key] = -1
        else:
            positions[key] = -1
        if key == "end" and positions[key] != -1:
            positions[key] = positions[key] + len(text)

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

    # Sort markers by position in descending order to avoid position shifts
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

def process_convo_text(transcript, riddle):
    try:
        riddle_data = get_ollama_output(transcript, riddle)
        if riddle_data:
            positions = calculate_positions(transcript, riddle_data)
            validate_riddle_positions(transcript, positions)
            return add_markers_to_transcript(transcript, positions)
        else:
            print("Failed to process the transcript accurately.")
            return transcript
    except Exception as e:
        print(f"An error occurred in process_convo_text: {e}")
        return transcript