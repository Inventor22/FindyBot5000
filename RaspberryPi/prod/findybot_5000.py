import openai
import os
import json
import speech_recognition as sr
from pocketsphinx import LiveSpeech
from elevenlabslib import *
import platform
from tenacity import retry, wait_random_exponential, stop_after_attempt
import requests
from termcolor import colored

from database import database
from serial_interface import SerialInterface, print_received_data
from item import Item
from color import Color

class FindyBot5000:
    def __init__(self, port: str) -> None:
        # Keyword identification and sentence detection
        # Sphinx has some trouble getting 'jarvis' every time...
        self.keywords = ['jarvis', 'jervis']

        # Large Language Model and speech to text - OpenAI 
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        openai.api_key = self.openai_key
        self.engine = "gpt-3.5-turbo-0613"

        # Voice synthesis - ElevenLabs
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        self.voice_name = "Rachel"
        self.recognizer = sr.Recognizer()
        self.speech = sr.Microphone(device_index=0)
        self.user = ElevenLabsUser(self.elevenlabs_key)
        self.voice = self.user.get_voices_by_name(self.voice_name)[0]  # This is a list because multiple voices can have the same name

        # SQL database
        self.db = database()

        # Serial port interface to communicate with Arduino
        if port is None:
            os_name = platform.system()

            if self.serial is None:
                if os_name == 'Linux':
                    self.serial = SerialInterface('dev/ttyACM0', 115200, print_received_data)
                elif os_name == 'Windows':
                    self.serial = SerialInterface('COM7', 115200, print_received_data)
            
            self.serial.open()
        else:
            self.serial = SerialInterface(port, 115200, print_received_data)
            self.serial.open()

        self.serial.clear_display()
        self.serial.set_relay(False)

        self.messages = []
        self.messages.append({
            "role": "system", 
            "content":
                "Don't make assumptions about what values to plug into functions. " + 
                "Ask for clarification if a user request is ambiguous or if a quantity is not specified as a number."})

        self.get_functions()

    def run(self) -> None:

        quit = False

        while not quit:
            # Step 0: Detect a human
            # todo
            
            try:
                # Step 1: Listen for the keyword
                #keyword_speech = LiveSpeech(lm=False, keyphrase='jarvis', kws_threshold=1e-20)
                print('Listening for Keyword...')
                keyword_speech = LiveSpeech()
                for phrase in keyword_speech:
                    words = str(phrase)
                    if any(keyword in words for keyword in self.keywords):# 'jarvis' in words or 'jervis' in words:
                        print(f'Heard a keyword! {self.keywords}')
                        break
                    elif 'print' in words or 'table' in words:
                        self.db.print_tables()
                    elif 'exit' in words or 'quit' in words or 'stop' in words:
                        quit = True
                        self.serial.close()
                        raise Exception("Quitting")
                    elif 'clear' in words:
                        self.serial.clear_display()
                        self.serial.set_relay(False)

                # Step 2: Listen for a sentence
                with self.speech as source:
                    print("Listening for a sentence...")
                    audio = self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source)
                
                # Step 3: Speech to Text
                print("Running speech to text with Whisper")
                whisper_text = self.recognizer.recognize_whisper_api(audio, model="whisper-1", api_key=self.openai_key)
                print(f"Whisper thinks you said: '{whisper_text}'")

                if whisper_text == '':
                    continue
                
                self.run_completion(whisper_text)


                
                # Step 4: Identify items from text using one of OpenAI's GPT LLM's
                human_response, json_response = self.get_responses(whisper_text)

                print(f"OpenAI human response: '{human_response}'")
                print(f"OpenAI json response: '{json_response}'")

                # Step 5: Use EleventLabs to synthesize a voice response for the item being looked for
                print("Generating and playing audio")
                self.voice.generate_and_play_audio(human_response, playInBackground=False)

                # Step 6: Use the json_response to update the database
                print("Updating database")
                cmd, items_to_display = self.update_database(json_response)

                # Step 7: Display the items
                print("Displaying items")
                self.display_items(cmd, items_to_display)

            except sr.UnknownValueError:
                print("Sphinx could not understand audio")
            except sr.RequestError as e:
                print(f"Sphinx error; {e}")
            except Exception as e:
                print(f"Ex: {e}")

    def update_database(self, json_response: str) -> list:
        try:
            parsed_json = json.loads(json_response)
            cmd = parsed_json['cmd']
            items = parsed_json['items']

            items_to_display = []

            if cmd == 'find':
                for item in items:
                    found_items = self.db.search_items(item)
                    for found_item in found_items:
                        items_to_display.append(found_item)

            elif cmd == 'add':
                for item in items:
                    added_or_updated_item = self.db.add_or_update_item(item)
                    for added_item in added_or_updated_item:
                        items_to_display.append(added_item)

            elif cmd == 'remove':
                items_deleted = self.db.delete_items2(items)
                for item in items_deleted:
                    items_to_display.append(item)
            else:
                print(f"Unexpected command: '{cmd}'")
            
            return cmd, items_to_display

        except json.JSONDecodeError:
            print("The string provided is not a valid JSON.")

    def display_items(self, cmd: str, items: list) -> None:
        
        if not self.serial.relay_on:
            print("Turning relay on")
            self.serial.set_relay(True)
    
        for item in items:
            print(item)
            
            if cmd == 'find':
                color = Color.LawnGreen
            elif cmd == 'add':
                color = Color.Cyan
            elif cmd == 'remove':
                color = Color.Red

            self.serial.set_box_color(item[Item.Row], item[Item.Col], color)

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages, functions=None, function_call=None, model=GPT_MODEL):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + openai.api_key,
        }
        json_data = {"model": model, "messages": messages}
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=json_data,
            )
            return response
        except Exception as e:
            print("Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            return e
        
    def pretty_print_conversation(self, messages):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        
        for message in messages:
            if message["role"] == "system":
                print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "user":
                print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and message.get("function_call"):
                print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and not message.get("function_call"):
                print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "function":
                print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

    def get_functions(self):
        self.functions = [
        {
            "name": "search_items",
            "description": "Search for items in the inventory database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to match item names",
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "add_or_update_item",
            "description": "Add a new item to the inventory or update it if it already exists",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The name of the item to add or update",
                    },
                    "additional_quantity": {
                        "type": "integer",
                        "description": "The additional quantity to add to the inventory (defaults to 1)",
                        "default": 1
                    }
                },
                "required": ["item_name"]
            }
        },
        {
            "name": "delete_items",
            "description": "Delete items from the inventory database",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "A list of item names to delete from the inventory",
                    }
                },
                "required": ["items"]
            }
        },
        {
            "name": "print_tables",
            "description": "Print the current state of the tables in the database",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "exit",
            "description": "Exit the program and close any open resources",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "clear_display",
            "description": "Clear the current display, turn off all the lights",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]
    
    def run_completion(self, text):
        self.messages.append({"role": "user", "content": text})
        chat_response = self.chat_completion_request(
            self.messages, functions=self.functions
        )
        assistant_message = chat_response.json()["choices"][0]["message"]
        self.messages.append(assistant_message)
        print(assistant_message)

        return assistant_message
    
    def execute_function_call(self, message):
        if message["function_call"]["name"] == "search_items":
            query = json.loads(message["function_call"]["arguments"])["query"]
            results = self.db.search_items(query)
        else:
            results = f"Error: function {message['function_call']['name']} does not exist"
        return results

    def get_responses(self, question: str) -> str:      

        language_prompt = \
            'You are a helpful assistant. A user will ask you to find, add, or remove items. Assume all items can be found.' + \
            'Reply with a friendly message. The message must mention the items. If there are no items, reply with an empty sentence. ' + \
            'Do not mention where the items are added or removed. It must be a single sentence.' + \
           f'Question: {question}'

        openai_response = openai.Completion.create(
            engine=self.engine,
            prompt=language_prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        language_response = openai_response["choices"][0]["text"].strip()

        json_prompt = \
            'You are a helpful assistant. You are asked to find, add, or remove items. Reply with json only. ' + \
            'If finding items, format as: { "cmd": "find", "items": ["red LEDs", "blue LEDs"] }. ' + \
            'If adding items, format as: { "cmd": "add", "items": ["green LEDs"] }. ' + \
            'If removing items, format as: { "cmd": "remove", "items": ["yellow LEDs", "twist ties", "9V battery"] }.' + \
           f'Question: {question}'
        
        openai_response = openai.Completion.create(
            engine=self.engine,
            prompt=json_prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        json_response = openai_response["choices"][0]["text"].strip()

        return language_response, json_response

