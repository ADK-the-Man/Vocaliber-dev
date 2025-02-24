import time
from flask import Flask, render_template, request, jsonify
import os
import speech_recognition as sr
from gtts import gTTS
import difflib
import subprocess
import re

app = Flask(__name__)

user_scores = {
    "speaking": [],
    "story": [],
    "reading": []
}

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

readers = [
    "Once upon a time there was a small village near a river where the people were kind and hardworking but one day an intruder arrived and killed a man named Rama who had a brother named Ramesh who was a police officer and during the investigation it was revealed that their stepbrother Raman was responsible for the murder so he was arrested and put behind bars"]

story = "Once upon a time, there was a small village near a river. The people there were very kind and hardworking. One intruder came in between and killed a person named Rama and Rama had a brother named Ramesh who is police officer. While investigating, it is declared that a person named Raman who is their step brother killed him. He was arrested and kept behind the bars"
questions = [
    {"question": "Where was the village located?", "options": ["Near a river", "On a mountain", "In a desert"], "answer": "Near a river"},
    {"question": "What were the people like?", "options": ["Lazy", "Kind and hardworking", "Angry"], "answer": "Kind and hardworking"},
    {"question": "Who was killed in the village?", "options": ["Rama","Raman","Raja","Ram"], "answer": "Rama"},
    {"question": "Who is the culprit and who is the police?", "options": ["Rama and Raja","Ramesh and Raman","Raman and Rama","Raman and Ramesh"], "answer":"Raman and Ramesh"}
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

@app.route('/story')
def story_page():
    return render_template('story.html', story=story, questions=questions)

@app.route('/reading')
def reading_page():
    return render_template('reading.html', readers=readers)


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

import hashlib

def generate_filename(text, extension="webm"):
    hash_object = hashlib.md5(text.encode())  # Generate hash for text
    return f"{hash_object.hexdigest()}.{extension}"

@app.route('/process_speech', methods=['POST'])
def process_speech():
    file = request.files['audio']
    sentence = request.form.get('sentence', 'unknown')
    module = request.form.get('module', 'speaking')  # Default to speaking module

    # Generate hashed filename
    input_filename = os.path.join(UPLOAD_FOLDER, generate_filename(sentence, "webm"))
    output_filename = input_filename.replace(".webm", ".wav")

    file.save(input_filename)

    # Convert WebM to WAV
    wav_file = convert_to_wav(input_filename, output_filename)
    if not wav_file:
        return jsonify({"error": "Failed to convert audio"}), 500

    spoken_text = speech_to_text(wav_file)
    similarity = calculate_similarity(sentence, spoken_text)

    # Store scores based on module
    if module in user_scores:
        user_scores[module].append(similarity)

    # Delete processed files
    os.remove(input_filename)
    os.remove(output_filename)

    return jsonify({"spoken_text": spoken_text, "similarity": similarity})


"""
@app.route('/process_speech', methods=['POST'])
def process_speech():
    file = request.files['audio']
    sentence = request.form.get('sentence', 'unknown')
    module = request.form.get('module', 'speaking')  # Default to speaking module

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

    # Store scores based on module
    if module in user_scores:
        user_scores[module].append(similarity)

    # Delete processed files
    os.remove(input_filename)
    os.remove(output_filename)

    return jsonify({"spoken_text": spoken_text, "similarity": similarity})
"""
@app.route('/speak_story', methods=['POST'])
def speak_story():
    audio_path = text_to_speech(story, "static/story.mp3")
    return jsonify({"audio": f"/{audio_path}?t={int(time.time())}"})  # Force refresh



@app.route('/submit_story', methods=['POST'])
def submit_story():
    if not user_scores["story"]:
        return jsonify({"error": "No story scores available"}), 400

    overall_story_score = sum(user_scores["story"]) / len(user_scores["story"])
    return render_template('result.html', overall_score=overall_story_score, scores=user_scores["story"])

@app.route('/submit_reading', methods=['POST'])
def submit_reading():
    if not user_scores["reading"]:
        return jsonify({"error": "No reading scores available"}), 400

    overall_reading_score = sum(user_scores["reading"]) / len(user_scores["reading"])
    return render_template('result.html', overall_score=overall_reading_score, scores=user_scores["reading"])

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if not any(user_scores.values()):  # Check if any module has scores
        return jsonify({"error": "No scores available"}), 400

    all_scores = []
    for module_scores in user_scores.values():
        all_scores.extend(module_scores)  # Flatten lists into one

    overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

    return render_template('result.html', overall_score=overall_score, scores=all_scores)


if __name__ == '__main__':
    app.run(debug=True)
