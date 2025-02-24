let mediaRecorder;
let audioChunks = [];
let currentIndex = 0;
let sentences = [];

document.addEventListener("DOMContentLoaded", function () {
    sentences = JSON.parse(document.getElementById("sentences-data").textContent);
    updateSentenceDisplay();

    window.playSentence = function () {
    let playButton = document.getElementById("playSentence");
    playButton.disabled = true;  // Disable after first click

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

    window.startRecording = function () {
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

                    formData.append('audio', audioBlob);
                    formData.append('sentence', sentences[currentIndex]);

                    fetch('/process_speech', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById("spoken-text").innerText = data.spoken_text;
                        document.getElementById("similarity").innerText = data.similarity.toFixed(2);

                        document.getElementById("stopRecord").style.display = "none";

                        if (currentIndex < sentences.length - 1) {
                            document.getElementById("nextSentence").style.display = "inline-block";
                        } else {
                            document.getElementById("submitTest").style.display = "inline-block";
                        }
                    });
                };
            });
    };

    window.stopRecording = function () {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
    };

    window.nextSentence = function () {
        let playButton = document.getElementById("playSentence");
        playButton.disabled = false;
        currentIndex++;
        if (currentIndex < sentences.length) {
            updateSentenceDisplay();
        }
    };

    window.submitTest = function () {
        fetch('/submit_test', { method: 'POST' })
            .then(response => response.text())
            .then(html => document.body.innerHTML = html);
    };

    function updateSentenceDisplay() {
        document.getElementById("sentence").innerText = sentences[currentIndex];
        document.getElementById("spoken-text").innerText = "";
        document.getElementById("similarity").innerText = "";

        document.getElementById("startRecord").style.display = "inline-block";
        document.getElementById("stopRecord").style.display = "none";
        document.getElementById("nextSentence").style.display = "none";
        document.getElementById("submitTest").style.display = "none";
    }
});
