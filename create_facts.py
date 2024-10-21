import logger_config
logging = logger_config.setup_logging()

import databasecon
import getResponseFromOllama
import re
import json
import kmcontroller
import convertToVideo

def getCustomInstruction():
    return f"""Start with 'Did you know...'
[Present each fact with engaging tone and short unexpected connections]
[Add a single wow/amazing/incredible reaction]
'Thank you for listening!'
Rules:
No acknowledging audience directly
Present facts sequentially without deviation
No additional commentary or explanations
Keep reactions short and impactful
Strictly follow sequence exactly"""

def getSource(facts, explain):
    return f'{facts}. {explain}'

def get_prompt():
    try:
        oldAnswers = ''
        result = databasecon.execute("SELECT answer FROM entries WHERE type = 'facts'")
        for (answer,) in result:
            oldAnswers += answer + ","

        prompt = f"""You are a master facts teller. Create ONE unique, clever, and engaging facts following these exact specifications:
The answer should NOT be any of these: {oldAnswers}
FORMAT: Return ONLY this exact JSON structure:
{{
    "title": "Engaging YouTube Shorts Title",
    "facts": "Your facts text here",
    "answer": "single word answer",
    "explaination":"your explain text here",
    "category": "pick one: Strange Historical Anecdotes/Science Wonders/Human Body Insights/Cultural Quirks/Mind-Bending Psychology/World Records/Food Trivia/Mysteries and Conspiracies"
}}

Facts GUIDELINES:
1. Make it ORIGINAL - never use common
2. Must be family-friendly and appropriate for all ages
3. Facts and explanation should be very short
4. Fact must be verifiable and accurate

TITLE REQUIREMENTS:
- Must be catchy and YouTube-optimized
- 3-5 words maximum"""
        logging.info(f"Prompt created successfully:: {prompt}")
        return prompt
    
    except Exception as e:
        logging.error(f"Error in get_prompt: {e}")
        return ""

def start():
    try:
        facts = databasecon.execute("SELECT * FROM entries WHERE type = 'facts' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        if facts is None:
            logging.info("No text puzzle is available")
            is_data_added = False
            when = 0
            while is_data_added is False:
                logging.info(f"Getting text from llama...")
                output = getResponseFromOllama.makeRequest(get_prompt())
                
                json_match = re.search(r'\{.*?\}', output, re.DOTALL)
                if json_match:
                    facts_data = json.loads(json_match.group())
                    logging.info(f"Facts generated: {facts_data}")

                    databasecon.execute("""INSERT into entries (audioPath, title, description, thumbnailText, answer, type) VALUES (?, ?, ?, ?, ?, ?)""", ('--', facts_data['title'], facts_data['facts'], facts_data['explaination'], facts_data['answer'], 'facts'))
                    is_data_added = True
                when += 1
                if when > 50:
                    return False
        
        facts = databasecon.execute("SELECT * FROM entries WHERE type = 'facts' AND (generatedVideoPath IS NULL OR generatedVideoPath = '')", type='get')
        logging.info(f"Starting to create text puzzle... {facts}")
        
        autio_path = kmcontroller.createAudioAndDownload(getCustomInstruction(), getSource(facts[3], facts[4]))
        
        is_success = convertToVideo.process(facts[0], autio_path)
        
        databasecon.execute(f"""
            UPDATE entries 
                SET audioPath = {'Done' if is_success else 'Failed'},
                generatedVideoPath = {'' if is_success else 'NULL'},
                generatedThumbnailPath = {'' if is_success else 'NULL'}
            WHERE id = ?
        """, (facts[0],))

    except Exception as e:
        logging.error(f"Error in createChessPuzzle::start : {str(e)}", exc_info=True)
        return False

    return is_success

if __name__ == "__main__":
    start()