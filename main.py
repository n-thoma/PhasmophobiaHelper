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

import streamlit.delta_generator
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler
from langchain_core.messages import HumanMessage, AIMessage
import json
import streamlit
import re

# ---------------------------------------------------------------------------------------------------------------------
#   config.json Extract Functions
# ---------------------------------------------------------------------------------------------------------------------

# Function to extract AI name
def get_name():
    with open("config/config.json", 'r') as file:
        data = json.load(file)
    return data.get("Assistant_Name")

# Function to extract GPT model to use
def get_gpt_model():
    with open("config/config.json", 'r') as file:
        data = json.load(file)
    return data.get("GPT_Model")

# Function to extract AI instructions
def get_instructions():
    with open("config/config.json", 'r') as file:
        data = json.load(file)
    return data.get("Assistant_Instructions")

# Function to extract filepaths for file_search tool
def get_file_paths():
    with open("config/config.json", 'r') as file:
        data = json.load(file)

    filepaths = []

    for path in data.get("File_Paths"):
        filepaths.append("data/" + path)

    return filepaths


# ---------------------------------------------------------------------------------------------------------------------
#   Streamlit Setup
# ---------------------------------------------------------------------------------------------------------------------

# Set page title and icon
streamlit.set_page_config(page_title="PolterText", page_icon="https://i.imgur.com/LLSQfET.png")

# Centering image
streamlit.markdown("<div style='text-align: center;'><img src='https://i.imgur.com/y1gj32C.png' width='150'/></div>", unsafe_allow_html=True)

# Centering title
streamlit.markdown("<h1 style='text-align: center;'>{} The Ghost Expert</h1>".format(get_name()), unsafe_allow_html=True)

# Some whitespace
streamlit.write("")
streamlit.write("")
streamlit.write("")

# API Key input
openai_api_key = ""
with streamlit.sidebar:
    openai_api_key = streamlit.text_input("Encrypted Address:", type="password")
    if not openai_api_key:
        streamlit.info("Please add your OpenAI API key to continue.", icon="🗝️")

# ---------------------------------------------------------------------------------------------------------------------
#   Assistant Setup
# ---------------------------------------------------------------------------------------------------------------------


if openai_api_key:
    # Init client with api key
    client = OpenAI(
        api_key = openai_api_key
    )

    # Init assistant with instructions, gpt model, and tools (function calls)
    phasmophobia_assistant = client.beta.assistants.create(
        name="Phasmophobia Assistant",
        instructions=str(get_instructions()),
        model=get_gpt_model(),
        tools=[
            {
                "type": "file_search"
            }
        ], 
    )

    vector_store = client.beta.vector_stores.create(name="Phasmophobia Data Vector Store")

    file_paths = get_file_paths()
    file_streams = [open(path, "rb") for path in file_paths]

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id,
        files=file_streams
    )

    phasmophobia_assistant = client.beta.assistants.update(
        assistant_id=phasmophobia_assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )    

    # Init thread
    thread = client.beta.threads.create()

# ---------------------------------------------------------------------------------------------------------------------
#   EventHandler class to define how to handle the events in the response stream.
# ---------------------------------------------------------------------------------------------------------------------

class EventHandler(AssistantEventHandler):    

    @override
    def on_event(self, event):
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.handle_requires_action(event.data, run_id)


    #@override
    #def on_message_delta(self, delta, message):
        #streamlit.write(message.content[0].text.value)


    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)


    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))


    # Handles function calls that require action
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

            # DEBUG :)
            # print(tool)
            # print(output_str)

            # Append output to tool_outputs arr
            tool_outputs.append({"tool_call_id": tool.id, "output": str(output_str)})

        self.submit_tool_outputs(tool_outputs, run_id)


    # Submits output from function calls to the assistant
    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=thread.id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler()
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

# Display the conversation history
for message in streamlit.session_state.chat_history:
    if isinstance(message, HumanMessage):
        with streamlit.chat_message("Human"):
            streamlit.markdown(message.content)
    else:
        with streamlit.chat_message("AI", avatar="https://i.imgur.com/y1gj32C.png"):
            streamlit.markdown(message.content)

# Input prompt from the user
if openai_api_key:
    user_prompt = streamlit.chat_input(f"Message {get_name()}:")

    if user_prompt is not None and user_prompt != "":

        # Add user's input to the session history
        streamlit.session_state.chat_history.append(HumanMessage(user_prompt))

        with streamlit.chat_message("Human"):
            streamlit.markdown(user_prompt)

        with streamlit.chat_message("AI", avatar="https://i.imgur.com/y1gj32C.png"):

            thinking_placeholder = streamlit.empty()
            thinking_placeholder.markdown("***Typing...***")

            # Check if thread_id is None, if so create a new thread, else retrieve the thread
            if streamlit.session_state.thread_id is None:
                thread = client.beta.threads.create()
                streamlit.session_state.thread_id = thread.id
            else:
                thread = client.beta.threads.retrieve(streamlit.session_state.thread_id)

            # Gets assistant response and removes any annotations
            assistant_response = get_assistant_response(user_prompt)
            assistant_response = re.sub(r"【.*?】", "", assistant_response)

            streamlit.markdown(assistant_response)

            thinking_placeholder.empty()

        streamlit.session_state.chat_history.append(AIMessage(assistant_response))
