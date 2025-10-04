# Use the official Matrix Synapse image as the base.
# This image contains all necessary binaries and dependencies.
FROM docker.io/matrixdotorg/synapse:v1.139.0

# === Custom Authentication Module Installation Section ===

# 1. Copy the local custom module files into the image.
# We assume the custom authentication module is in a local directory named 'custom_synapse_module'.
# IMPORTANT: This directory MUST contain the necessary files (like setup.py/pyproject.toml)
# to be recognized as an installable Python package.
WORKDIR /src

COPY ./custom_auth ./custom_auth
COPY pyproject.toml .

# 3. Use pip to install your package from the source code
RUN pip install .
# ==========================================

COPY ./firebase_creds.json /etc/firebase_creds.json
# Set the environment variable to ensure Synapse looks for its configuration
# at the standard location inside the container, which is often mounted 
# to a persistent volume at runtime.
ENV SYNAPSE_CONFIG_PATH=/data/homeserver.yaml

# The application is already configured to run by default in the base image.
# No further CMD or ENTRYPOINT changes are usually needed.

