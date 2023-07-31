const form = document.getElementById("message-form");
const chatContainer = document.getElementById("chat-container");
const submitButton = document.getElementById("submit-button");

function showBotTyping() {
    const typingMessage = document.createElement("div");
    typingMessage.textContent = "Bot is typing ...";
    typingMessage.classList.add("message", "received", "typing");
    chatContainer.appendChild(typingMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
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
      const response = await fetch("/send_message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userInput,
        }),
      });

      const data = await response.text();
      if (data.trim() !== "") {
        appendMessage("Sorry, I can't do that yet.", true);
      }
      appendMessage(data, true);
    } catch (error) {
      console.error("Error sending message:", error);
    }
    submitButton.disabled = false;
  }
});
