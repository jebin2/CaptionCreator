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

def get_chess_prompt(transcript, corrected_moves=True):
    if corrected_moves:
        return f"""Extract and validate chess moves from the transcript, formatting them as paired move sets in JSON.
If an invalid move is found, correct it based on the subsequent valid moves to maintain game continuity.

Required format:
{{
    "move1": {{
        "white": "<White's move in algebraic notation>",
        "black": "<Black's move in algebraic notation>"
    }}
}}

Rules:
1. Use standard algebraic notation (SAN) (e.g., e4, Nf6, O-O)
2. Each move set must contain both White's and Black's moves together
3. For invalid moves:
   - Analyze the subsequent valid moves
   - Correct the invalid move to maintain game flow
   - Ensure the correction leads to the known valid position
4. Keep all valid moves unchanged
5. For castling, use uppercase 'O' (not zero)

Note: Output should pair White and Black moves together in each move set, not split them across different move numbers.

Transcript: {transcript}"""
    else:
        return """Extract and validate chess moves from the transcript, formatting them in JSON.

Required format:
{{
    "move1": {{
        "white": "<move in algebraic notation>",
        "black": "<move in algebraic notation>"
    }}
}}

Rules:
1. Use standard algebraic notation (SAN) (e.g., e4, Nf6, O-O)
2. Keep all valid moves unchanged
3. For castling, use uppercase 'O' (not zero)
4. Maintain exact JSON structure

Note: Give me the moves as it is, don't worry about the mistake

Transcript: {transcript}
"""

def get_chess_puzzel_prompt(riddle, answer, transcript, verify):
    return f"""
        Analyze the following transcription and extract the exact text for these elements:

        Answer: {answer}
        Transcription: {transcript}

        CRITICAL: You must ONLY respond with a JSON object. Do not include ANY other text, explanation, or formatting.
        The response must be in this exact format:

        {{
            "answer": "extracted text for riddle answer"
        }}

        Extraction rules:
        1. Riddle Answer: The exact text where the solution is first mentioned or explained. Look for any clear solution indication.
        
        Note: 
        - Be precise in identifying these text excerpts
        - Extract only the specific riddle question or statement, not general discussion

        {verify}
    """


def parse(prompt):
    try:
        print(f"Prompt: {prompt}")
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
        print("Final output")
        print(f"{content}")

        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            riddle_data = json.loads(json_match.group())
            return riddle_data
    
    except Exception as e:
        print(f"Error in parse: {e}")
    
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
        logging.info(f"Ollama response content: {content}")

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

# if __name__ == "__main__":
    # transcript = """Hello, everyone. Today's chess puzzle. The board position is NF3, NF6, D4, E6, BG5, B7, QD2, OO, C4, B6, N5, N6, G3, NB8, F4, A5. Okay. So it's blacks turned to move, got having just captured the pawn on H7. Okay. Let's let's get this going. All right. That capture on 8, 7 is interesting. Yeah. It seems counterintuitive. It does, doesn't it? They give up a pawn like that. Exactly. Black is playing a risky gambit here, sacrificing material for potential positional advantage. Okay. What's fascinating here is why H7? Right. It seems innocuous. Yeah. But it sets up a series of moves that can quickly turn the tide in black's favor. So for things like black here, what's the immediate goal? Checkmate. Really? Oh, yeah. The H7 pawn capture was just the opening act. Wow. Now the real drama begins. Notice how the board is primed for black to develop their pieces rapidly. I see what you mean. Yeah. It's almost like black is inviting white to make a mistake. Precisely. And the most tempting move for white here, the one that looks like it breaks black's attack is actually the path to their downfall. Oh, wow. You've got me on the edge of my seat here. Okay. What's the winning sequence? The answer is RxF1 checkmate. Wow. A rook sacrifice to deliver a checkmate. Yeah. I did not see that coming. It's a tricky one. E4 E5, QH5, NC6, BG5, BD, B7, knee 2o. So black lures white into this false sense of security. Exactly. And then bam checkmate. Old spray. Thank you for listening. My pleasure."""
    # parse(get_chess_puzzel_prompt("Nf3 Nf6; d4 e6; Bg5 Be7; Qd2 O-O; c4 b6; Ne5 Na6; g3 Nb8; f4 a5", "Rxf1", transcript, ''))
    # parse("""Hello everyone, today's mystery. I'm always coming but never arrive. In a cycle I'm forever alive. I bring you speed but also delay. My presence is felt in a modern way. Let's unlock this mystery. It's always coming but never arrive. That feels like something constantly in motion, right? Something that's always on his way but never actually reaches a final destination. Yes, and the phrase in a cycle reinforces that idea of continuous movement. This isn't a one-time event, it's a repeating pattern. And look at this speed but also delay. That's a fascinating contradiction. Whatever this is, it has the power to both accelerate and hinder progress. Precisely. And the final clue, presence is felt in a modern way. Suggest that this is something relevant to our current times. Likely a concept or force we grapple with in our daily lives. Putting it all together, the answer is traffic. It fits because traffic is always flowing, never truly ending, and can either speed up or delay our journeys in our modern world. Thank you for listening.""",  get_prompt("I'm always coming but never arrive, In a cycle, I'm forever alive. I bring you speed, but also delay, My presence is felt, in a modern way.", "TRAFFIC", transcript, ''))