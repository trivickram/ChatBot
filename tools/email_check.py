import os
from pathlib import Path

print('Checking email configuration presence (values are masked):')
email_env = os.getenv('EMAIL_SENDER')
pass_env = os.getenv('EMAIL_PASSWORD')
print('EMAIL_SENDER present in environment:', bool(email_env))
print('EMAIL_PASSWORD present in environment:', bool(pass_env))

secrets_file = Path('.streamlit') / 'secrets.toml'
print('.streamlit/secrets.toml exists:', secrets_file.exists())

# If st.secrets were available this script would need streamlit runtime, but we avoid executing that here.
print('\nNotes:')
print('- If credentials are stored in .streamlit/secrets.toml, Streamlit apps read them as st.secrets, but env vars may still be empty.')
print('- This check avoids printing any secret values.')
