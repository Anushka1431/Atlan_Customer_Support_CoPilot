import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    audio_headers = headers.copy()
    audio_headers["Content-Type"] = "audio/mpeg"  # for mp3 files

    response = requests.post(
        API_URL,
        headers=audio_headers,
        data=audio_bytes
    )

    if response.status_code != 200:
        raise Exception(f"HF API Error: {response.status_code}, {response.text}")

    output = response.json()
    return output.get("text", output)  # return transcription text if available

if __name__ == "__main__":
    audio_file = "D:/anushka/Atlan_Project/data/Recording.mp3"
    print(f"Transcribing {audio_file} ...")
    result = transcribe_audio(audio_file)
    print("Transcription Result:\n", result)
    
