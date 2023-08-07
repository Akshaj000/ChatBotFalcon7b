const form = document.getElementById("message-form");
const uploadForm = document.getElementById("upload-form");
const chatContainer = document.getElementById("chat-container");
const submitButton = document.getElementById("submit-button");

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
    fetch('/send_message', {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: userInput,
      }),
    }) // Make a request to /new endpoint to reset the conversation
    .then(response => {
      if (response.status === 200){
        return response.text()
      } else {
        return "Ops! try again."
      }
    })
    .then(data => {
      appendMessage(data, true);
    })
    .catch(error => console.error("Error resetting conversation:", error));
    submitButton.disabled = false;
  }
});


uploadForm.addEventListener("change", async function (e) {
    e.preventDefault();
    appendMessage("Uploading file...", true)
    const formData = new FormData(uploadForm);
    const file = formData.get("file");
    const fileInput = document.getElementById("file-input");
    fileInput.disabled = true;
    if (file) {
        fetch('/upload', {
            method: "POST",
            body: formData,
        })
        .then(response => {
            fileInput.disabled = false;
            if (response.status !== 200){
                uploadForm.reset();
                return response.text()
            }
            return "File uploaded successfully! You can ask questions based on the file."
        })
        .then(data => {
            appendMessage(data, true);
        })
        .catch(error => console.error("Error resetting conversation:", error));
    }
});
