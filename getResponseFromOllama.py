import requests
import ollamaresponseparser
import json
import re
from logger_config import setup_logging

logging = setup_logging()

def makeRequest(prompt):
    try:
        logging.info(f"Prompt: {prompt}")
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
        logging.info(f"ollama output {content}")
        return content
    
    except Exception as e:
        print(f"Error in parse: {e}")
    
    return None

# if __name__ == "__main__":
#     transcript = """Hello, everyone. Today's chess puzzle. The board position is NF3, NF6, D4, E6, BG5, B7, QD2, OO, C4, B6, N5, N6, G3, NB8, F4, A5. Okay. So it's blacks turned to move, got having just captured the pawn on H7. Okay. Let's let's get this going. All right. That capture on 8, 7 is interesting. Yeah. It seems counterintuitive. It does, doesn't it? They give up a pawn like that. Exactly. Black is playing a risky gambit here, sacrificing material for potential positional advantage. Okay. What's fascinating here is why H7? Right. It seems innocuous. Yeah. But it sets up a series of moves that can quickly turn the tide in black's favor. So for things like black here, what's the immediate goal? Checkmate. Really? Oh, yeah. The H7 pawn capture was just the opening act. Wow. Now the real drama begins. Notice how the board is primed for black to develop their pieces rapidly. I see what you mean. Yeah. It's almost like black is inviting white to make a mistake. Precisely. And the most tempting move for white here, the one that looks like it breaks black's attack is actually the path to their downfall. Oh, wow. You've got me on the edge of my seat here. Okay. What's the winning sequence? The answer is RxF1 checkmate. Wow. A rook sacrifice to deliver a checkmate. Yeah. I did not see that coming. It's a tricky one. E4 E5, QH5, NC6, BG5, BD, B7, knee 2o. So black lures white into this false sense of security. Exactly. And then bam checkmate. Old spray. Thank you for listening. My pleasure."""
    # makeRequest(get_chess_puzzel_prompt("Nf3 Nf6; d4 e6; Bg5 Be7; Qd2 O-O; c4 b6; Ne5 Na6; g3 Nb8; f4 a5", "Rxf1", transcript, ''))
    # makeRequest("""Hello everyone, today's mystery. I'm always coming but never arrive. In a cycle I'm forever alive. I bring you speed but also delay. My presence is felt in a modern way. Let's unlock this mystery. It's always coming but never arrive. That feels like something constantly in motion, right? Something that's always on his way but never actually reaches a final destination. Yes, and the phrase in a cycle reinforces that idea of continuous movement. This isn't a one-time event, it's a repeating pattern. And look at this speed but also delay. That's a fascinating contradiction. Whatever this is, it has the power to both accelerate and hinder progress. Precisely. And the final clue, presence is felt in a modern way. Suggest that this is something relevant to our current times. Likely a concept or force we grapple with in our daily lives. Putting it all together, the answer is traffic. It fits because traffic is always flowing, never truly ending, and can either speed up or delay our journeys in our modern world. Thank you for listening.""",  get_prompt("I'm always coming but never arrive, In a cycle, I'm forever alive. I bring you speed, but also delay, My presence is felt, in a modern way.", "TRAFFIC", transcript, ''))