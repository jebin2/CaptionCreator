import json
from logger_config import setup_logging
import re

logging = setup_logging()

def getUrl():
    with open('ollamadetails.json', 'r') as file:
        ollamadetails = json.load(file)
        return ollamadetails["URL"]

def replace_multiple_spaces(content):
    # Replace multiple spaces with a single space while preserving newlines
    content = re.sub(r'```', ' ', content)
    return re.sub(r'\s+', ' ', content)

def getParsedData(response):
    # Parse the response
    lines = response.splitlines()
    json_objects = []
    for line in lines:
        try:
            json_object = json.loads(line)  # Convert to dictionary
            json_objects.append(json_object)  # Add to the list
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e} for line: {line}")
    new_content = ''.join(replace_multiple_spaces(item['message']['content']) for item in json_objects)
    return replace_multiple_spaces(new_content)