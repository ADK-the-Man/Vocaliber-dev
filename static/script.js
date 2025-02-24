let mediaRecorder;
let audioChunks = [];
let currentIndex = 0;
let sentences = [];
let questions = [];
let readingSentences = [];
let currentModule = "speaking"; // Default module

document.addEventListener("DOMContentLoaded", function () {
    // Load sentences (for speaking module)
    let sentenceData = document.getElementById("sentences-data");
    if (sentenceData) {
        sentences = JSON.parse(sentenceData.textContent);
        updateSentenceDisplay();
    }

    // Load questions (for story module)
    let questionData = document.getElementById("questions-data");
    if (questionData) {
        questions = JSON.parse(questionData.textContent);
        updateStoryQuestionDisplay();
    }

    // Load reading sentences
    let readingData = document.getElementById("reading-data");
    if (readingData) {
        readingSentences = JSON.parse(readingData.textContent);
        updateReadingDisplay();
    }
});

// 🎙️ Play Sentence (Speaking Module)
window.playSentence = function () {
    let playButton = document.getElementById("playSentence");
    playButton.disabled = true;  // Prevent multiple clicks

    fetch('/speak_sentence', {
        method: 'POST',
        body: JSON.stringify({ sentence: sentences[currentIndex] }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        let audio = new Audio(data.audio);
        audio.play();
    });
};

// 📖 Play Story (Story Module)
window.playStory = function () {
    fetch('/speak_story', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        let audio = new Audio(data.audio);
        audio.play();
    });
};

// 🎤 Start Recording (Handles all modules)
window.startRecording = function (module = "speaking") {
    currentModule = module;
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorder.start();
            audioChunks = [];

            document.getElementById("startRecord").style.display = "none";
            document.getElementById("stopRecord").style.display = "inline-block";

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                let audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                let formData = new FormData();

                let textToCompare = "";
                if (module === "speaking") textToCompare = sentences[currentIndex];
                if (module === "story") textToCompare = questions[currentIndex].answer;
                if (module === "reading") textToCompare = readingSentences[currentIndex];

                formData.append('audio', audioBlob);
                formData.append('sentence', textToCompare);
                formData.append('module', module); // Identify the module

                fetch('/process_speech', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (module === "speaking") {
                        document.getElementById("spoken-text").innerText = data.spoken_text;
                        document.getElementById("similarity").innerText = data.similarity.toFixed(2);
                    } else if (module === "story") {
                        document.getElementById("story-answer").innerText = data.spoken_text;
                        document.getElementById("story-similarity").innerText = data.similarity.toFixed(2);
                    } else if (module === "reading") {
                        document.getElementById("reading-text").innerText = data.spoken_text;
                        document.getElementById("reading-similarity").innerText = data.similarity.toFixed(2);
                    }

                    document.getElementById("stopRecord").style.display = "none";
                    if (currentIndex < sentences.length - 1 || currentIndex < questions.length - 1) {
                        document.getElementById("nextSentence").style.display = "inline-block";
                    } else {
                        document.getElementById("submitTest").style.display = "inline-block";
                    }
                });
            };
        });
};

// 🛑 Stop Recording
window.stopRecording = function () {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
};

// ➡️ Next Sentence / Question
window.nextSentence = function () {
    let playButton = document.getElementById("playSentence");
    playButton.disabled = false;
    currentIndex++;

    if (currentModule === "speaking" && currentIndex < sentences.length) {
        updateSentenceDisplay();
    } else if (currentModule === "story" && currentIndex < questions.length) {
        updateStoryQuestionDisplay();
    } else if (currentModule === "reading" && currentIndex < readingSentences.length) {
        updateReadingDisplay();
    }
};

// 📤 Submit Story-Based Questions
window.submitStory = function () {
    fetch('/submit_story', { method: 'POST' })
    .then(response => response.text())
    .then(html => document.body.innerHTML = html);
};

// 📤 Submit Reading Assessment
window.submitReading = function () {
    fetch('/submit_reading', { method: 'POST' })
    .then(response => response.text())
    .then(html => document.body.innerHTML = html);
};

// 📤 Submit Test (Speaking Module)
window.submitTest = function () {
    fetch('/submit_test', { method: 'POST' })
    .then(response => response.text())
    .then(html => document.body.innerHTML = html);
};

// 🔄 Update Display Functions

function updateSentenceDisplay() {
    document.getElementById("sentence").innerText = sentences[currentIndex];
    document.getElementById("spoken-text").innerText = "";
    document.getElementById("similarity").innerText = "";

    document.getElementById("startRecord").style.display = "inline-block";
    document.getElementById("stopRecord").style.display = "none";
    document.getElementById("nextSentence").style.display = "none";
    document.getElementById("submitTest").style.display = "none";
}

// ➡️ Next Story Question
window.nextQuestion = function () {
    currentIndex++;

    if (currentIndex < questions.length) {
        updateStoryQuestionDisplay(); // Update display for the next question
    }

    // If it's the last question, hide "Next Question" and show "Submit Test"
    let nextButton = document.getElementById("nextQuestion");
    let submitButton = document.getElementById("submitStory");

    if (nextButton) {
        nextButton.style.display = currentIndex < questions.length - 1 ? "inline-block" : "none";
    }
    
    if (submitButton) {
        submitButton.style.display = currentIndex === questions.length - 1 ? "inline-block" : "none";
    }
};

// 🔄 Update Story Questions Display
function updateStoryQuestionDisplay() {
    let container = document.getElementById("questions-container");

    if (!container) {
        console.error("Element 'questions-container' not found.");
        return;
    }

    let optionsHTML = "<p><strong>Options:</strong></p><ul>";
    questions[currentIndex].options.forEach(option => {
        optionsHTML += `<li>${option}</li>`;
    });
    optionsHTML += "</ul>";

    container.innerHTML = `
        <h3>Question ${currentIndex + 1}: ${questions[currentIndex].question}</h3>
        ${optionsHTML}
        <button id="startRecord" onclick="startRecording('story')">Answer with Speech</button>
        <button id="stopRecord" onclick="stopRecording()" style="display:none;">Stop Recording</button>
        <p><strong>Your Answer:</strong> <span id="story-answer"></span></p>
        <p><strong>Similarity:</strong> <span id="story-similarity"></span>%</p>
        <button id="nextQuestion" onclick="nextQuestion()" style="display:${currentIndex < questions.length - 1 ? 'inline-block' : 'none'};">Next Question</button>
    `;

    let submitButton = document.getElementById("submitStory");
    if (submitButton) {
        submitButton.style.display = currentIndex === questions.length - 1 ? "inline-block" : "none";
    }
}



function updateReadingDisplay() {
    document.getElementById("reading-sentence").innerText = readingSentences[currentIndex];
    document.getElementById("reading-text").innerText = "";
    document.getElementById("reading-similarity").innerText = "";

    document.getElementById("startReadingRecord").style.display = "inline-block";
    document.getElementById("submitReading").style.display = "inline-block";
}
