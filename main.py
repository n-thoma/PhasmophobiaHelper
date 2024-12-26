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
from langchain_core.messages import HumanMessage, AIMessage
import json
import streamlit

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
                "description": "Outputs data about a specific ghost of a given name. Data includes: evidence needed, strengths, weaknesses, description, and notes about the ghost.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "enum": ["Spirit", "Poltergeist", "Mare", "Demon", "Yokai", "Myling", "Raiju", "Moroi", "Wraith", "Banshee", "Revenant", "Yurei", "Hantu", "Onryo", "Obake", "Deogen", "Phantom", "Jinn", "Shade", "Oni", "Goryo", "The Twins", "The Mimic", "Thaye"],
                            "description": "The name of the ghost you want to learn about."
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_evidence_data",
                "description": "Outputs data about a specific evidence type of a given name. Data includes: Ghost Proven With, descriptions, mechanics, and notes about the evidence type. Does NOT talk about the equipment! Only talks about the evidence itself.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "enum": ["D.O.T.S. Projector", "Ghost Writing", "EMF Level 5", "Ghost Orbs", "Ultraviolet", "Freezing Temperatures", "Spirit Box"],
                            "description": "The name of the evidence you want to learn about."
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_ghosts_from_evidence",
                "description": "Outputs a list of possible ghosts from the given evidence name. Use this if user asks something like: What ghosts can be proven with EMF Level 5?",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "enum": ["D.O.T.S. Projector", "Ghost Writing", "EMF Level 5", "Ghost Orbs", "Ultraviolet", "Freezing Temperatures", "Spirit Box"],
                            "description": "The name of the evidence."
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_ghosts_from_keyword",
                "description": "Outputs every ghost and its data that contains the given keyword in its data. Only searches for results in ghosts; not evidence, not equipment, not cursed items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "description": "The keyword or phrase you want to search for. Highly recommended to keep this 1 word, but short phrases allowed too. Examples: 'fast', 'slow', 'hunt', 'breath'"
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_equipment_data",
                "description": "Outputs data about a equipment of a given name. Data includes: description, mechanics, data on the different tiers, and other notes about the equipment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "enum": ["D.O.T.S. Projector", "EMF Reader", "Ghost Writing Book", "Spirit Box", "Thermometer", "UV Light", "Video Camera", "Flashlight", "Crucifix", "Firelight", "Head Gear", "Igniter", "Incense", "Motion Sensor", "Parabolic Microphone", "Photo Camera", "Salt", "Sanity Medication", "Sound Sensor", "Tripod"],
                            "description": "The name of the equipment you want to learn about."
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_cursed_item_data",
                "description": "Outputs data about a cursed item of a given name. Data includes: description, mechanics, and other notes about the cursed item",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "enum": ["Haunted Mirror", "Monkey Paw", "Music Box", "Ouija Board", "Summoning Circle", "Tarot Cards", "Voodoo Doll"],
                            "description": "The name of the cursed item you want to learn about."
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_equipment_from_keyword",
                "description": "Outputs every equipment and its data that contains the given keyword in its data. Only searches for results in equipment; not evidence, not ghost, not cursed items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "description": "The keyword or phrase you want to search for. Highly recommended to keep this 1 word, but short phrases allowed too. Examples: 'freezing', 'glitch', 'head', 'blind'"
                        }
                    },
                    "required": ["arg"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_cursed_item_from_keyword",
                "description": "Outputs every cursed item and its data that contains the given keyword in its data. Only searches for results in cursed items; not evidence, not equipment, not ghosts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "arg": {
                            "type": "string",
                            "description": "The keyword or phrase you want to search for. Highly recommended to keep this 1 word, but short phrases allowed too. Examples: 'sanity', 'ghost', 'hunt', 'ghost room'"
                        }
                    },
                    "required": ["arg"]
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
    results = []

    # Iterates through ghosts and all its elements, searching for keyword
    for ghost in data["ghosts"]:

        for evidence in ghost["evidence"]:
            if keyword in evidence.lower():
                results.append(f"Found {keyword} in {ghost["name"]} in Evidence: {ghost["evidence"]}")

        if keyword.lower() in ghost["strengths"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Strengths: {ghost["strengths"]}")
        if keyword.lower() in ghost["weaknesses"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Weaknesses: {ghost["weaknesses"]}")
        if keyword.lower() in ghost["game_description"].lower():
            results.append(f"Found {keyword} in {ghost["name"]} in Game Description: {ghost["game_description"]}")

        for note in ghost["notes"]:
            if keyword.lower() in note["title"].lower():
                results.append(f"Found {keyword} in {ghost["name"]} in a Note titled {note["title"]}: {note["description"]}")
            if keyword.lower() in note["description"].lower():
                results.append(f"Found {keyword} in {ghost["name"]} in a Note titled {note["title"]}: {note["description"]}")

    return results


# Gets information on equipment given a key word
def search_cursed_item_from_keyword(keyword):
    results = []

    # Iterates through cursed items and all its elements, searching for keyword
    for cursed_item in data["cursed_items"]:

        if keyword in cursed_item["description"]:
            results.append(f"Found {keyword} in {cursed_item["name"]} in Description: {cursed_item["description"]}")
        if keyword in cursed_item["mechanics"]:
            results.append(f"Found {keyword} in {cursed_item["name"]} in Mechanics: {cursed_item["mechanics"]}")

        for note in cursed_item["notes"]:
            if keyword.lower() in note["title"].lower():
                results.append(f"Found {keyword} in {cursed_item["name"]} in a Note titled {note["title"]}: {note["description"]}")
            if keyword.lower() in note["description"].lower():
                results.append(f"Found {keyword} in {cursed_item["name"]} in a Note titled {note["title"]}: {note["description"]}")

    return results


# Gets information on cursed item given a key word
def search_equipment_from_keyword(keyword):
    results = []

    # Iterates through evidences and all its elements, searching for keyword
    for evidence in data["evidences"]:

        for ghost in evidence["ghosts_proven_with"]:
            if keyword in ghost.lower():
                results.append(f"Found {keyword} in {evidence["name"]} in Ghosts Proven With: {evidence["ghosts_proven_with"]}")

        if keyword in evidence["game_description"]:
            results.append(f"Found {keyword} in {evidence["name"]} in Game Description: {evidence["game_description"]}")
        if keyword in evidence["wiki_description"]:
            results.append(f"Found {keyword} in {evidence["name"]} in Wiki Description: {evidence["wiki_description"]}")
        if keyword in evidence["mechanics"]:
            results.append(f"Found {keyword} in {evidence["name"]} in Mechanics: {evidence["mechanics"]}")

        for note in evidence["notes"]:
            if keyword.lower() in note["title"].lower():
                results.append(f"Found {keyword} in {evidence["name"]} in a Note titled {note["title"]}: {note["description"]}")
            if keyword.lower() in note["description"].lower():
                results.append(f"Found {keyword} in {evidence["name"]} in a Note titled {note["title"]}: {note["description"]}")

    return results


# Gets equipment json data from the given name
def get_equipment_data(equipment_name):
    for equipment in data["equipment"]:
        if equipment["name"].lower() == equipment_name.lower():
            return equipment
        

# Gets cursed item json data from the given name
def get_cursed_item_data(item_name):
    for item in data["cursed_items"]:
        if item["name"].lower() == item_name.lower():
            return item
        

# ---------------------------------------------------------------------------------------------------------------------
#   EventHandler class to define how to handle the events in the response stream.
# ---------------------------------------------------------------------------------------------------------------------

class EventHandler(AssistantEventHandler):    

    @override
    def on_event(self, event):
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.handle_requires_action(event.data, run_id)


    def handle_requires_action(self, data, run_id):
        tool_outputs = []

        # For all tools that require action
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            arg = json.loads(tool.function.arguments).get("arg")
            output_str = ""

            # Extract function and call it with proper arg
            try:
                func = globals().get(tool.function.name)
                if callable(func):
                    output_str = func(str(arg))
                    
            except AttributeError:
                print(f"{tool.function.name} is not callable.")

            print(tool)
            print(output_str)

            # Append output to tool_outputs arr
            tool_outputs.append({"tool_call_id": tool.id, "output": str(output_str)})

        self.submit_tool_outputs(tool_outputs, run_id)


    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=thread.id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()


# ---------------------------------------------------------------------------------------------------------------------

# Function to get assistant response
def get_assistant_response(prompt):
    # Send user message to the thread
    client.beta.threads.messages.create(thread.id, role="user", content=prompt)

    # Start a run
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=phasmophobia_assistant.id, 
        event_handler=EventHandler()
    ) as stream:
        stream.until_done()

    # Get the latest messages in the thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value


# Chat history container
if 'chat_history' not in streamlit.session_state:
    streamlit.session_state.chat_history = []

# Thread ID container (store id in session state to preserve thread)
if 'thread_id' not in streamlit.session_state:
    streamlit.session_state.thread_id = None


streamlit.set_page_config(page_title="G.H.O.S.T.", page_icon="👻")
streamlit.title("Ghost Hunting Operations and Survival Tool")

# Display the conversation history
for message in streamlit.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with streamlit.chat_message("Human"):
            streamlit.markdown(message.content)
    else:
        with streamlit.chat_message("AI"):
            streamlit.markdown(message.content)

# Input prompt from the user
user_prompt = streamlit.chat_input("Enter your prompt:")

if user_prompt is not None and user_prompt != "":

    # Add user's input to the session history
    streamlit.session_state.chat_history.append(HumanMessage(user_prompt))

    with streamlit.chat_message("Human"):
        streamlit.markdown(user_prompt)

    with streamlit.chat_message("AI"):
        # Check if thread_id is None, if so create a new thread, else retrieve the thread
        if streamlit.session_state.thread_id is None:
            thread = client.beta.threads.create()
            streamlit.session_state.thread_id = thread.id
        else:
            thread = client.beta.threads.retrieve(streamlit.session_state.thread_id)

        assistant_response = get_assistant_response(user_prompt)
        streamlit.markdown(assistant_response)

    streamlit.session_state.chat_history.append(AIMessage(assistant_response))