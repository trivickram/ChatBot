// scripts.js
document.getElementById('notesForm').addEventListener('submit', function(event) {
  event.preventDefault();

  const formData = new FormData();
  const fileInput = document.getElementById('notesFile');
  const candidateName = document.getElementById('candidateName').value;

  formData.append('notesFile', fileInput.files[0]);
  formData.append('candidateName', candidateName);

  fetch('/candidate-notes/', {
      method: 'POST',
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      if (data.summary) {
          document.getElementById('summaryText').textContent = data.summary;
      } else if (data.error) {
          document.getElementById('summaryText').textContent = 'Error: ' + data.error;
      }
  })
  .catch(error => {
      document.getElementById('summaryText').textContent = 'An error occurred: ' + error.message;
  });
});
