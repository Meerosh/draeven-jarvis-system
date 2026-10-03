async function sendToJarvis(message) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: 'draeven-session-1',
      task_type: 'general'
    })
  });

  if (!response.ok) {
    throw new Error('Jarvis API request failed');
  }

  const data = await response.json();
  return data.reply;
}

async function handlePrompt(userInput) {
  try {
    const reply = await sendToJarvis(userInput);
    console.log(reply);
    return reply;
  } catch (error) {
    console.error(error);
    return 'Jarvis is unavailable right now. Check the local API server.';
  }
}

// Example call:
// const result = await handlePrompt('Plan my next business week');
