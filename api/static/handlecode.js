function appendMessage(content, isReceived) {
  const messageElement = document.createElement("div");
  messageElement.classList.add("message");

  // Check if the message contains code blocks wrapped inside triple backticks
  const codeBlockRegex = /```(\w*)\s*([\s\S]*?)```/g;
  const containsCodeBlocks = codeBlockRegex.test(content);

  if (isReceived) {
    messageElement.classList.add("received");
  }

  if (containsCodeBlocks) {
    // Treat the part inside triple backticks as a code block
    const parts = content.split(codeBlockRegex);
    console.log(parts)
    parts.forEach((part, index) => {
      const messagePart = document.createElement("span");
      if (index % 3 === 1) {
        // Treat odd-indexed parts as code blocks
        const language = parts[index];
        const codeContainer = document.createElement("div");
        codeContainer.className = `code-container language-${language || 'plaintext'}`;

        const codeBlock = document.createElement("pre");
        const code = document.createElement("code");
        code.textContent = parts[index + 1]; // Code content is at odd-indexed part
        codeBlock.appendChild(code);
        codeContainer.appendChild(codeBlock);

        // Create the copy button
        const copyButton = document.createElement("button");
        copyButton.className = "copy-button";
        copyButton.textContent = "Copy";
        copyButton.addEventListener("click", () => {
          // Copy the code block content to the clipboard
          navigator.clipboard.writeText(parts[index + 1]);
        });

        // Append the copy button to the code container
        codeContainer.appendChild(copyButton);
        messagePart.appendChild(codeContainer);
      } else if (index % 3 !== 2) {
        messagePart.textContent = part;
      }
      messageElement.appendChild(messagePart);
    });
  } else {
    // Display the message normally if no code blocks are found
    messageElement.textContent = content;
  }

  chatContainer.appendChild(messageElement);
  Prism.highlightAllUnder(chatContainer);
  chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to the bottom
  const typingMessage = chatContainer.querySelector(".message.received.typing");
  if (typingMessage) {
    typingMessage.remove();
  }
}
