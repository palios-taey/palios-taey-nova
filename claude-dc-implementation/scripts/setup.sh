#!/bin/bash

# Conductor Framework Setup Script
# This script installs all required dependencies for the Conductor Framework

echo "Setting up Conductor Framework environment..."

# Create Python virtual environment
python3 -m venv /home/computeruse/github/palios-taey-nova/claude-dc-implementation/.venv
source /home/computeruse/github/palios-taey-nova/claude-dc-implementation/.venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install \
    numpy \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    streamlit \
    tensorflow \
    anthropic \
    openai \
    google-cloud-firestore \
    google-api-python-client \
    google-auth \
    python-dotenv \
    requests \
    flask \
    pymilvus \
    transformers \
    nltk \
    python-sonic \
    pillow \
    fastapi \
    uvicorn[standard] \
    spacy \
    PyWavelets \
    librosa

# Install spaCy language model
python -m spacy download en_core_web_md

# Create .env file with API keys
cat > /home/computeruse/github/palios-taey-nova/claude-dc-implementation/.env << EOL
ANTHROPIC_API_KEY="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"
GOOGLE_AI_STUDIO_KEY="AIzaSyDwJUPzaV39IGDMQMmsbSZy5eI2tWStJMs"
OPENAI_API_KEY="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"
XAI_GROK_API_KEY="xai-9O7QlpoIhG0Amvbiuy7c5Yd3S5MrHwLzAfqy5RxoLcejT9UHOCaAmpn5XuCc6XaMsQjUuLT9ASxJ7Kdy"

# GCP Service Account credentials
GCP_PROJECT_ID="palios-taey-dev"
GCP_REGION="us-central1"
EOL

# Setup Google Cloud credentials
mkdir -p /home/computeruse/github/palios-taey-nova/claude-dc-implementation/credentials
cat > /home/computeruse/github/palios-taey-nova/claude-dc-implementation/credentials/service_account.json << EOL
{
  "type": "service_account",
  "project_id": "palios-taey-dev",
  "private_key_id": "297eb532dcf59faa76cec230dd84a69a6b7d4cf6",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCQ9ajdVxpo5XoJ\nNFsnGpwwR15janiLonBDrwIyjMvP5KmzxyvaKbqnWPhQshJkv7x31mWSx+8iWouk\n1FJK/TbW8ObgxKibUwO5lnY/LPUmFc5SHcFgfQa4RyRy3SIdJADbP3dl2ddYzUXw\nzAmrG7wWLBu3/+h+Dtvk6zqQh0bKwxO/aBJpQAqjOUtZAFcWWGsLekju8NJJBnWK\nYZ13ts5t734Ql+8KJKBddh5zU7idd/ssMzFBoq3sVzjR8OE1nYN0WcIffAU1ysBQ\n2Rs/VlcqIAjXDQLMaRzY4ODywi7gd+PZ2Nb3RPobx051d2cZ5ZZRx3alxve4wWZB\nQZP3FQ6dAgMBAAECggEACS0LwesUGGTCS1fdl0WXcnTqFCf2tnwTWC15WaLQ+flz\nBpbKf1ZZ4uL+YPlMscTzVLClIFv4lredlFL+XJHXyVZZfwvj0mU4XKSaGpipcf46\nX7dTeNyhMsQKGh1GXgrb5QUI9VELUSs5TKtVx1eLmemz3XtdB7HAGKcNP33YrNgB\nAGIZ5gfE5GWZV7/XHAoh5Ge4ceZYgdj4EZNYruh8wdseSuUm4wgnT2rUcDqD72P2\nIksUpg+lKhz3Mi4bNUjGndBERzUi4wwAGiK/2KwNlcbZtKFGjJJVxgua8l/O2c1G\nX8v626NHjv7n76CMVkupPwW4Wz6VMryugRlmRC/ZwQKBgQDFJ36Do/7aw6bsZDVo\natmZeMesImQaPZAFJWfsqHYx9XkGIJmpIqcYDG6xq5n3PGLwXH3Ov0hKGZB82NTc\ndkHjDTxZoyzj/ujKai5MbKvAkVmeHUpOTbGSoDVZ0rBgWhQOODNvWXv4FWRgXjep\ntdBwDJ8oEcHXxrfS6EhEZp0I/QKBgQC8OfwdXz0+DmDtW/V9SXSkD2+DXhKSVCBk\nFKqQTdaF7PI/aUFFjbOBvXlZRsmS2z3ce6XGp3vaaYYDZG8GLG39u3KPnFdkluDH\nZRZeLYoFWBujYDDoCA6+jtqsjZZf74DrYSNns58oNLOGueJYaeoLC43bTtErV4Z9\nm8+KxNJeIQKBgQCRWHNpoy5QoyrdXWcOSq+O+D7kBRqdScNyN8hs7Sjt3dVSEhiW\nW2iqTwgQTb0dStR59QX+tIAbuMsPb19GBJzAQdK7FpQSpauDBlKJnxfjyIQ0D83m\n+louCZQrWysSbXYZoY8xyNue4k50ySDqKZK3+GYhSS4J4INGpl4YpzmgFQKBgQCF\nh+lIeRE8Xfz7RpqwiBT8corcujcYoh/cgCDEgMPofMEapTQOAMnRB7b309UanviS\n2xEvDhA6UVQmQfDVg12AfKN4KCSDktnh+t/UbiAVTH1G+O2ZHmY/X57YfRWp94IQ\n+fehEPefEUwvDt35dSH5NfgsFg0j31Lk901UF+v9ZoQKBgD6Q/dFRAU3sujGsv9e1\nwHzYX33f4p/jkzxF7lnxkB2Rn054Q9B9ShfV5vB8O0oxfcwz6qc5Wzp/cI0jFGGo\nUnyrn9859bFDKmXX9kZhwwackJ2Y/LWCZDvWVBkRPeWS0+owYCbU0cvkj1fm9hYUE\ndMAR+QRl6k5DNEg/h8Im/hS3\n-----END PRIVATE KEY-----\n",
  "client_email": "the-conductor-service@palios-taey-dev.iam.gserviceaccount.com",
  "client_id": "113453704497780463215",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/the-conductor-service%40palios-taey-dev.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
EOL

# Create config directory
mkdir -p /home/computeruse/github/palios-taey-nova/claude-dc-implementation/config

# Create sample transcript directory
mkdir -p /home/computeruse/github/palios-taey-nova/claude-dc-implementation/data/transcripts

echo "Environment setup complete!"