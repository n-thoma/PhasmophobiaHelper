# ---------------------------------------------------------------------------------------------------------------------
#
#   File:         main.py
#   Author:       Nathaniel Thoma
#   Description:  Functionality of a chatbot using OpenAI's Beta Assistants API that helps players with their
#                 Phasmophobia experience.
#
#   API Documentation Here:  https://platform.openai.com/docs/assistants/overview
#   Phasmophobia:            https://store.steampowered.com/app/739630/Phasmophobia/
#   Phasmophobia Wiki:       https://phasmophobia.fandom.com/wiki/Main_Page
#
# ---------------------------------------------------------------------------------------------------------------------

from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
import json

# ---------------------------------------------------------------------------------------------------------------------
#   config.json Extract Functions
# ---------------------------------------------------------------------------------------------------------------------

# Function to extract API key
def get_api_key():
    with open("config.json", 'r') as file:
        data = json.load(file)
    return data.get("API_Key")

# Function to extract GPT model to use
def get_gpt_model():
    with open("config.json", 'r') as file:
        data = json.load(file)
    return data.get("GPT_Model")

# Function to extract AI instructions
def get_instructions():
    with open("config.json", 'r') as file:
        data = json.load(file)
    return data.get("Assistant_Instructions")

# ---------------------------------------------------------------------------------------------------------------------
#   Assistant Setup
# ---------------------------------------------------------------------------------------------------------------------

# Init client with api key
client = OpenAI(
    api_key = str(get_api_key())
)

# Init assistant with instructions, gpt model, and tools (function calls)
phasmophobia_assistant = client.beta.assistants.create(
    name="Phasmophobia Assistant",
    instructions=str(get_instructions()),
    model=get_gpt_model(),
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_ghost_data",
                "description": "Gives you, the AI assistant information on a Phasmophobia ghost of your choice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ghost_name": {
                            "type": "string",
                            "enum": ["Spirit", "Poltergeist", "Mare", "Demon", "Yokai", "Myling", "Raiju", "Moroi", "Wraith", "Banshee", "Revenant", "Yurei", "Hantu", "Onryo", "Obake", "Deogen", "Phantom", "Jinn", "Shade", "Oni", "Goryo", "The Twins", "The Mimic", "Thaye"],
                            "description": "The ghost you want to learn about."
                        }
                    },
                    "required": ["ghost_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_evidence_data",
                "description": "Gives you, the AI assistant information on a Phasmophobia evidence of your choice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "evidence_name": {
                            "type": "string",
                            "enum": ["D.O.T.S. Projector", "Ghost Writing", "EMF Level 5", "Ghost Orbs", "Ultraviolet", "Freezing Temperatures", "Spirit Box"],
                            "description": "The evidence you want to learn about."
                        }
                    },
                    "required": ["evidence_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_ghosts_from_evidence",
                "description": "Gives you, the AI assistant a list of ghosts that a given evidence can prove.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "evidence_name": {
                            "type": "string",
                            "enum": ["D.O.T.S. Projector", "Ghost Writing", "EMF Level 5", "Ghost Orbs", "Ultraviolet", "Freezing Temperatures", "Spirit Box"],
                            "description": "The evidence name."
                        }
                    },
                    "required": ["evidence_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_ghosts_from_keyword",
                "description": "Gives you, the AI assistant a the ability to search for a ghost using a keyword.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "The keyword or phrase you want to search for. Highly recommended to keep this 1 word."
                        }
                    },
                    "required": ["keyword"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_equipment_data",
                "description": "Gives you, the AI assistant information on a Phasmophobia equipment of your choice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "equipment_name": {
                            "type": "string",
                            "enum": ["Crucifix", "Firelight", "Head Gear", "Igniter", "Incense", "Motion Sensor", "Parabolic Microphone", "Photo Camera", "Salt", "Sanity Medication", "Sound Sensor", "Tripod"],
                            "description": "The equipment you want to learn about."
                        }
                    },
                    "required": ["equipment_name"]
                }
            }
        }
    ] 
)

# Init thread
thread = client.beta.threads.create()

# ---------------------------------------------------------------------------------------------------------------------
#   Ghost Data Helper Functions
# ---------------------------------------------------------------------------------------------------------------------

# Open ghost_data.json for read
with open("ghost_data.json", "r") as file:
    data = json.load(file)


# Gets ghost json data from given name
def get_ghost_data(ghost_name):
    for ghost in data["ghosts"]:
        if ghost["name"].lower() == ghost_name.lower():
            return ghost


# Gets evidence json data from the given name
def get_evidence_data(evidence_name):
    for evidence in data["evidences"]:
        if evidence["name"].lower() == evidence_name.lower():
            return evidence
        

# Gets list of ghosts from given evidence name
def get_ghosts_from_evidence(evidence_name):
    for evidence in data["evidences"]:
        if evidence["name"].lower() == evidence_name.lower():
            return evidence["ghosts_proven_with"]


# Gets information on ghosts given a key word
def search_ghosts_from_keyword(keyword):

    # Stores all results here
    results = []

    # Iterates through ghosts
    for ghost in data["ghosts"]:

        # Searches for keyword in strengths
        if keyword.lower() in ghost["strengths"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Strengths: {ghost["strengths"]}")

        # Searches for keyword in weaknesses
        if keyword.lower() in ghost["weaknesses"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Weaknesses: {ghost["weaknesses"]}")

        # Searches for keyword in the game description
        if keyword.lower() in ghost["game_description"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Game Description: {ghost["game_description"]}")

        # Iterates through notes
        for note in ghost["notes"]:

            # Searches for keyword in note title
            if keyword.lower() in note["title"].lower():
                results.append(f"Found {keyword} in {ghost["name"]} in a Note titled {note["title"]}: {note["description"]}")

            # Searches for keyword in the note body
            if keyword.lower() in note["description"].lower():
                results.append(f"Found {keyword} in {ghost["name"]} in a Note titled {note["title"]}: {note["description"]}")

    # Return results
    return results


# Gets equipment json data from the given name
def get_equipment_data(equipment_data):
    for equipment in data["equipment"]:
        if equipment["name"].lower() == equipment_data.lower():
            return equipment
        

# EventHandler class to define how to handle the events in the response stream.
class EventHandler(AssistantEventHandler):    

    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    #@override
    #def on_text_created(self, text) -> None:
    #    print(f"\nassistant > ", end="", flush=True)
        
    #@override
    #def on_text_delta(self, delta, snapshot):
    #    print(delta.value, end="", flush=True)
        
    #def on_tool_call_created(self, tool_call):
    #    if tool_call.type == 'function':
    #        print(tool_call)

    def handle_requires_action(self, data, run_id):

        # This will be submitted to tool outputs later
        tool_outputs = []

        # For all tools that require action
        for tool in data.required_action.submit_tool_outputs.tool_calls:

            # Extract args
            args = json.loads(tool.function.arguments)
            
            # Where output will be stored
            output_str = ""

            # Call proper function
            if tool.function.name == "get_ghost_data":
                output_str = get_ghost_data(args.get("ghost_name"))
            elif tool.function.name == "get_evidence_data":
                output_str = get_evidence_data(args.get("evidence_name"))
            elif tool.function.name == "get_ghosts_from_evidence":
                output_str = get_ghosts_from_evidence(args.get("evidence_name"))
            elif tool.function.name == "search_ghosts_from_keyword":
                output_str = search_ghosts_from_keyword(args.get("keyword"))

        print(tool)
        print(output_str)

        # Append output to tool_outputs arr
        tool_outputs.append({"tool_call_id": tool.id, "output": str(output_str)})

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)


    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.current_run.thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()


# Always update the thread with user and bot back-and-forth
while True:

    prompt = input("Enter a prompt: ")
    client.beta.threads.messages.create(thread.id,
                                        role="user",
                                        content=prompt)

    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=phasmophobia_assistant.id,
        event_handler=EventHandler()
    ) as stream:
      stream.until_done()


    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print("Assistant: " + messages.data[0].content[0].text.value)
