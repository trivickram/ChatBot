document.getElementById('chatbotForm').addEventListener('submit', function(event) {
  event.preventDefault();
  const question = document.getElementById('question').value;
  fetch('/submit-question', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question })
  })
  .then(response => response.json())
  .then(data => {
      document.getElementById('summaryText').value = data.answer;
  })
  .catch(error => {
      console.error('Error:', error);
      document.getElementById('summaryText').value = 'An error occurred. Please try again later.';
  });
});
