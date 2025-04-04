#!/bin/bash

# Run the communication dashboard
echo "Starting Communication Dashboard..."
streamlit run dashboard_app.py --server.port=8502
