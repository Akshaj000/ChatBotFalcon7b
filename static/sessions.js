function toggleMenu() {
  const dropDownMenu = document.getElementById("dropdown-menu");
  dropDownMenu.style.display = dropDownMenu.style.display !== "block" ? "block" : "none";
}


function updateSession(sessionId, newName) {
  fetch('/update-session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      name: newName,
    }),
  })
    .then(response => response.json())
    .then(data => {
      // Handle the response data if needed
      updateSessionUI(sessionId, newName, 'update'); // Update UI
    })
    .catch(error => {
      console.error('Error updating session:', error);
    });
}

function deleteSession(sessionId) {
  fetch('/delete-session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  })
    .then(response => {
      if (response.ok) {
        // Session deleted successfully
        // You might want to update the UI accordingly
        updateSessionUI(sessionId, null, 'delete'); // Remove from UI
      } else {
        console.error('Failed to delete session');
      }
    })
    .catch(error => {
      console.error('Error deleting session:', error);
    });
}