const form = document.getElementById("message-form");
const chatContainer = document.getElementById("chat-container");

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
      appendMessage(data, true);
    } catch (error) {
      console.error("Error sending message:", error);
    }

    form.reset();
  }
});
