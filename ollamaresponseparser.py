import json

def getUrl():
    with open('ollamadetails.json', 'r') as file:
        ollamadetails = json.load(file)
        return ollamadetails["URL"]

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
    return ''.join(item['message']['content'] for item in json_objects)