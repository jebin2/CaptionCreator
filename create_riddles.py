import json
import re
import sqlite3
import kmcontroller
from logger_config import setup_logging
import requests
import ollamaresponseparser
import databasecon

logging = setup_logging()


START_WITH = 'Hello everyone'

def getCustomInstruction(answer):
    return f"""Start with "{START_WITH}, Today's mystery"
[State riddle - Host1 and Host2 alternate reading each sentence]
Let's unlock this mystery...
[Break down the clues by analyzing and thinking out loud]
[gather insights]
[Arrive at the answer] The answer is: {answer}
There you go, [Quick one sentence explanation]
"Thank you for listening"
Rules:
Never acknowledge listener
Direct solving only
Strictly follow sequence exactly
1-2 minutes min-max time limit
No extra commentary"""

def getSource(riddle):
    return riddle

def get_prompt():
    try:
        result = databasecon.execute("SELECT answer FROM entries where type = 'text'")
        for (answer,) in result:
            oldAnswers += answer + ","

        prompt = f"""You are a master riddle creator. Create ONE unique, clever, and engaging riddle following these exact specifications:
The answer should NOT be any of these: {oldAnswers}
FORMAT: Return ONLY this exact JSON structure:
{{
    "title": "Engaging YouTube Title",
    "riddle": "Your riddle text here",
    "answer": "single word answer",
    "difficulty": "medium",
    "category": "pick one: nature/concepts/funny/clever/Mystery/Wordplay/facts-based/food",
    "hint": "optional subtle hint"
}}

RIDDLE GUIDELINES:
1. Make it ORIGINAL - never use common
2. Length: 3-4 lines that rhyme
3. Difficulty: Challenging but solvable
4. Style: Use clever wordplay, metaphors, or double meanings
5. Topic: Focus on traditional, relatable objects or concepts
6. Must be family-friendly and appropriate for all ages

TITLE REQUIREMENTS:
- Must be catchy and YouTube-optimized
- Include words like "How","What","Tricky," or "Can You Solve"
- 3-5 words maximum"""
        logging.info(f"Prompt created successfully:: {prompt}")
        return prompt
    
    except Exception as e:
        logging.error(f"Error in get_prompt: {e}")
        return ""

def get_ollama_output():
    try:
        prompt = get_prompt()

        response = requests.post(ollamaresponseparser.getUrl(), json={
            'model': 'llama3.1',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        })
        response.raise_for_status()
        
        content = ollamaresponseparser.getParsedData(response.text)
        logging.info(f"Ollama response content: {content}")

        # Extract JSON data using regex
        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            riddle_data = json.loads(json_match.group())
            logging.info(f"Riddle generated: {riddle_data}")
            return riddle_data
        else:
            logging.warning("No valid JSON format found in the response.")
    
    except Exception as e:
        logging.error("Error in get_ollama_output: %s", str(e), exc_info=True)
    
    return None

def start(riddle_data=None):
    try:
        hasRiddleAlready = False
        if riddle_data is not None:
            hasRiddleAlready = True
        riddle_data = riddle_data if hasRiddleAlready else get_ollama_output()
        if riddle_data:
            logging.info("Riddle generation succeeded.")
            riddle_data['audio_path'] = kmcontroller.createAudioAndDownload(getCustomInstruction(riddle_data['answer']), getSource(riddle_data["riddle"]))

            if hasRiddleAlready:
                databasecon.execute("""
                    UPDATE entries 
                    SET audioPath = ?
                    WHERE id = ?
                """, (riddle_data['audio_path'], riddle_data['id']))
            else:
                databasecon.execute("""INSERT into entries (audioPath, title, description, thumbnailText, answer, type) VALUES (?, ?, ?, ?, ?, ?)""", (riddle_data['audio_path'], riddle_data['title'], riddle_data['riddle'], riddle_data['riddle'], riddle_data['answer'], 'text'))

                databasecon.execute("""INSERT into entries (audioPath, title, description, thumbnailText, answer, type) VALUES (?, ?, ?, ?, ?, ?)""", ('--', riddle_data['title'], riddle_data['riddle'], '', riddle_data['answer'], 'facts'))

            return True
    
    except Exception as e:
        logging.error(f"An error occurred in start: {e}")

    return False