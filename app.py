import time
from flask import Flask, render_template, request, jsonify
import os
import speech_recognition as sr
from gtts import gTTS
import difflib
import subprocess
import re

app = Flask(__name__)

# Ensure necessary folders exist
UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Sample Data
sentences = [
    "Hello How are you",
    "The weather is nice today"
]


story = "Once upon a time, there was a small village near a river. The people there were very kind and hardworking."
questions = [
    {"question": "Where was the village located?", "options": ["Near a river", "On a mountain", "In a desert"], "answer": "Near a river"},
    {"question": "What were the people like?", "options": ["Lazy", "Kind and hardworking", "Angry"], "answer": "Kind and hardworking"}
]

# Function to generate speech from text
def text_to_speech(text, filename="static/output.mp3"):
    tts = gTTS(text)
    tts.save(filename)
    return filename

# Convert WebM to WAV using ffmpeg
def convert_to_wav(input_path, output_path):
    try:
        subprocess.run(["ffmpeg", "-i", input_path, "-ac", "1", "-ar", "16000", output_path], check=True)
        return output_path
    except subprocess.CalledProcessError:
        return None

# Function to recognize speech
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Error with speech recognition service"

# Function to calculate similarity
def calculate_similarity(original, spoken):
    return difflib.SequenceMatcher(None, original.lower(), spoken.lower()).ratio() * 100

@app.route('/')
def index():
    return render_template('index.html', sentences=sentences, story=story, questions=questions)

@app.route('/speak_sentence', methods=['POST'])
def speak_sentence():
    data = request.get_json()
    sentence = data['sentence']
    
    tts = gTTS(sentence)
    audio_path = os.path.join("static", "output.mp3")

    # Force overwrite the file
    if os.path.exists(audio_path):
        os.remove(audio_path)  # Delete the old file first

    tts.save(audio_path)

    return jsonify({"audio": f"/static/output.mp3?t={int(time.time())}"})  # Force refresh with timestamp

user_scores = []

@app.route('/process_speech', methods=['POST'])
def process_speech():
    file = request.files['audio']
    sentence = request.form.get('sentence', 'unknown')
    safe_sentence = re.sub(r'\W+', '_', sentence)
    input_filename = os.path.join(UPLOAD_FOLDER, f"{safe_sentence}.webm")
    output_filename = input_filename.replace(".webm", ".wav")

    file.save(input_filename)

    # Convert WebM to WAV
    wav_file = convert_to_wav(input_filename, output_filename)
    if not wav_file:
        return jsonify({"error": "Failed to convert audio"}), 500

    spoken_text = speech_to_text(wav_file)
    similarity = calculate_similarity(sentence, spoken_text)

    # Store the score
    user_scores.append(similarity)

    # Delete processed files
    os.remove(input_filename)
    os.remove(output_filename)

    return jsonify({"spoken_text": spoken_text, "similarity": similarity})

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if not user_scores:
        return jsonify({"error": "No scores available"}), 400

    overall_score = sum(user_scores) / len(user_scores)  # Calculate average score
    return render_template('result.html', overall_score=overall_score, scores=user_scores)

if __name__ == '__main__':
    app.run(debug=True)
