import ollama
import json
import re
import sqlite3
import logging
import kmcontroller

# Setup logging configuration
logging.basicConfig(filename='riddle_generation.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_prompt():
    try:
        oldAnswers = ''
        conn = sqlite3.connect('ContentData/entries.db')
        cursor = conn.cursor()
        cursor.execute("SELECT answer FROM entries")
        result = cursor.fetchall()
        for (answer,) in result:
            oldAnswers += answer + ","
        
        # Close the connection
        conn.close()

        prompt = f"""
            Create a unique, original riddle that has not been used before. The answer should NOT be any of these: {oldAnswers}

            Please format your response as:
            {{
                "title": <SEO optimised title for the riddle to upload in youtube>
                "riddle": <your new riddle>,
                "answer": <the solution>
            }}
        """
        logging.debug("Prompt created successfully.")
        return prompt
    
    except Exception as e:
        logging.error(f"Error in get_prompt: {e}")
        return ""

def get_ollama_output():
    try:
        prompt = get_prompt()
        if not prompt:
            return None

        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        content = response.get('message', {}).get('content', '')
        logging.debug(f"Ollama response content: {content}")

        # Extract JSON data using regex
        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            riddle_data = json.loads(json_match.group())
            logging.info(f"Riddle generated: {riddle_data}")
            return riddle_data
        else:
            logging.warning("No valid JSON format found in the response.")
    
    except Exception as e:
        logging.error(f"Error in get_ollama_output: {e}")
    
    return None

def insertData(riddle_data):
    try:
        conn = sqlite3.connect('ContentData/entries.db')
        cursor = conn.cursor()
        cursor.execute("""INSERT into entries (audioPath, title, description, thumbnailText, answer) VALUES (?, ?, ?, ?, ?)""", (riddle_data['audio_path'], riddle_data['title'], riddle_data['riddle'], riddle_data['riddle'], riddle_data['answer']))

        conn.commit()
        conn.close()
        logging.error(f"InsertData success: {riddle_data}")
        return True
    
    except Exception as e:
        logging.error(f"Error in insertData: {e}")
    
    return False

def start():
    try:
        riddle_data = get_ollama_output()
        if riddle_data:
            logging.info("Riddle generation succeeded.")
            riddle_data['audio_path'] = kmcontroller.createAudioAndDownload()
            if riddle_data['audio_path'] is None:
                return False
            return insertData(riddle_data)
    
    except Exception as e:
        logging.error(f"An error occurred in start: {e}")

    return False