import openai
import os
import json
import speech_recognition as sr
from pocketsphinx import LiveSpeech
from elevenlabslib import *
from database import database

class FindyBot5000:
    def __init__(self) -> None:
        # Keyword identification and sentence detection
        # Sphinx has some trouble getting 'jarvis' every time...
        self.keywords = ['jarvis', 'jervis']

        # Large Language Model and speech to text - OpenAI 
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        openai.api_key = self.openai_key
        self.engine = "text-davinci-003"

        # Voice synthesis - ElevenLabs
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        self.voice = "Rachel"

        # SQL database
        self.db = database()


    def run(self) -> None:
        r = sr.Recognizer()
        speech = sr.Microphone(device_index=0)
        user = ElevenLabsUser(self.elevenlabs_key)
        voice = user.get_voices_by_name(self.voice)[0]  # This is a list because multiple voices can have the same name

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
                    elif 'print' in words:
                        self.db.print_tables()
                    elif 'exit' in words or 'quit' in words:
                        quit = True
                        raise Exception("Quitting")

                # Step 2: Listen for a sentence
                with speech as source:
                    print("Listening for a sentence...")
                    audio = r.adjust_for_ambient_noise(source)
                    audio = r.listen(source)
                
                # Step 3: Speech to Text
                print("Running speech to text with Whisper")
                whisper_text = r.recognize_whisper_api(audio, model="whisper-1", api_key=self.openai_key)
                print(f"Whisper thinks you said: '{whisper_text}'")

                if whisper_text == '':
                    continue
                
                # Step 4: Identify items from text using one of OpenAI's GPT LLM's
                human_response, json_response = self.get_responses(whisper_text)

                print(f"OpenAI human response: '{human_response}'")
                print(f"OpenAI json response: '{json_response}'")

                # Step 5: Use EleventLabs to synthesize a voice response for the item being looked for
                voice.generate_and_play_audio(human_response, playInBackground=False)

                # Step 6: Use the json_response to update the database
                items_to_display = self.update_database(json_response)

                # Step 7: Display the items
                self.display_items(items_to_display)

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
                    added_or_updated_item = self.db.add_or_update_item(item, 1)
                    items_to_display.append(added_or_updated_item)

            elif cmd == 'remove':
                items_deleted = self.db.delete_items2(items)
                for item in items_deleted:
                    items_to_display.append(item)
            else:
                print(f"Unexpected command: '{cmd}'")
            
            return items_to_display

        except json.JSONDecodeError:
            print("The string provided is not a valid JSON.")

    def display_items(self, items: list) -> None:
        print("Processed Items:")
        for item in items:
            print(item)

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

