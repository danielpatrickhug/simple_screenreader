import asyncio
import Cocoa
from openai import OpenAI
import tempfile
import os
from pygame import mixer
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Config:
    API_KEY = os.environ.get("OPENAI_API_KEY")
    if not API_KEY:
        raise ValueError("API key not found. Set the OPENAI_API_KEY environment variable.")
    AUDIO_MODEL = "tts-1"
    AUDIO_VOICE = "echo"
    MAX_TEXT_SIZE = 4096

class TTSClient:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    async def text_to_speech(self, text, audio_queue):
        text_batches = self.split_text_into_batches(text, Config.MAX_TEXT_SIZE)
        tasks = [self.process_batch(batch, audio_queue) for batch in text_batches]
        await asyncio.gather(*tasks)

    async def process_batch(self, batch, audio_queue):
        try:
            response = self.client.audio.speech.create(
                model=Config.AUDIO_MODEL,
                voice=Config.AUDIO_VOICE,
                input=batch
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
                response.stream_to_file(temp_audio_file.name)
                temp_audio_path = temp_audio_file.name
                logging.info(f"Generated audio file: {temp_audio_path}")
                await audio_queue.put(temp_audio_path)
        except Exception as e:
            logging.error(f"Error occurred during API request: {e}")

    def split_text_into_batches(self, text, max_size):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        batches = []
        current_batch = ""

        for sentence in sentences:
            if len(current_batch) + len(sentence) <= max_size:
                current_batch += sentence + " "
            else:
                batches.append(current_batch.strip())
                current_batch = sentence + " "

        if current_batch:
            batches.append(current_batch.strip())

        return batches

class AudioPlayer:
    def __init__(self):
        mixer.init()

    async def play_audio(self, audio_queue):
        while True:
            audio_path = await audio_queue.get()
            mixer.music.load(audio_path)
            mixer.music.play()
            while mixer.music.get_busy():
                await asyncio.sleep(0.1)
            os.remove(audio_path)
            audio_queue.task_done()

class ClipboardListener:
    @staticmethod
    def get_pasteboard_text():
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_(Cocoa.NSPasteboardTypeString)
        return text

    @staticmethod
    def clear_pasteboard():
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        pasteboard.clearContents()

async def main():
    logging.info("Starting screen reader...")
    audio_queue = asyncio.Queue()

    tts_client = TTSClient(api_key=Config.API_KEY)
    audio_player = AudioPlayer()

    playback_task = asyncio.create_task(audio_player.play_audio(audio_queue))

    ClipboardListener.clear_pasteboard()

    try:
        while True:
            await asyncio.sleep(0.1)
            text = ClipboardListener.get_pasteboard_text()
            if text:
                logging.info(f"Highlighted text: {text}")
                asyncio.create_task(tts_client.text_to_speech(text, audio_queue))
                ClipboardListener.clear_pasteboard()
    except KeyboardInterrupt:
        logging.info("Exiting...")

    await audio_queue.join()
    playback_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
