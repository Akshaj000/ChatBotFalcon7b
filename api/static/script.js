const form = document.getElementById("message-form");
const uploadForm = document.getElementById("upload-form");
const chatContainer = document.getElementById("chat-container");
const submitButton = document.getElementById("submit-button");
const fileInput = document.getElementById('file-input');

function showBotTyping() {
    const typingMessage = document.createElement("div");
    typingMessage.textContent = "Bot is typing ...";
    typingMessage.classList.add("message", "received", "typing");
    chatContainer.appendChild(typingMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function resetConversation() {
  appendMessage("Resetting conversation...", true);
  chatContainer.innerHTML = ''; // Clear chat history
  fetch('/new') // Make a request to /new endpoint to reset the conversation
    .then(response => {
      if (response.status === 200){
          uploadForm.reset();
          return "Greetings! you can start by typing 'hi' or 'hello'"
      } else {
          return response.text()
      }
    })
    .then(data => {
      appendMessage(data, true);
    })
    .catch(error => console.error("Error resetting conversation:", error));
}

form.addEventListener("submit", async function (e) {
  e.preventDefault();
  const formData = new FormData(form);
  const userInput = formData.get("human_input");
  if (userInput.trim() !== "") {
    appendMessage(userInput, false);
    showBotTyping();
    submitButton.disabled = true;
    form.reset();
    try {
        const response = await fetch('/send_message', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message: userInput,
            }),
        })
        const data = await response.json();
        appendMessage(data.message, true);
    } catch (error) {
        console.error("Error sending message:", error);
    }
    submitButton.disabled = false;
  }
});


function checkUploadStatus() {
  fetch('/check-upload')
    .then(response => response.text())
    .then(status => {
      if (status === 'UPLOADED') {
          fileInput.disabled = false;
          submitButton.disabled = false;
          appendMessage('File is uploaded successfully.', true);
      } else if (status === "NOT_UPLOADED") {
          fileInput.disabled = false;
          submitButton.disabled = false;
          appendMessage('File upload failed. Please try again.', true);
      } else {
          setTimeout(checkUploadStatus, 5000)
      }
    })
    .catch(error => console.error('Error checking upload status:', error));
}


// Modify the uploadForm event listener to include the checkUploadStatus function
uploadForm.addEventListener('change', async function (e) {
  e.preventDefault();
  const formData = new FormData(uploadForm);
  const file = formData.get('file');
  fileInput.disabled = true;
  submitButton.disabled = true;
  if (file) {
    fetch('/upload', {
      method: 'POST',
      body: formData,
    })
      .then(response => {
        if (response.status !== 200) {
          uploadForm.reset();
          return response.text();
        }
        return 'File is uploading. Please wait...';
      })
      .then(data => {
        appendMessage(data, true);
        checkUploadStatus(); // Start checking the upload status
      })
      .catch(error => console.error('Error uploading file:', error));
  }
});
