#!/bin/bash
# Run both apps simultaneously
echo "Starting Missing Persons AI System..."
echo ""
echo "Desktop App  → http://localhost:8501"
echo "Mobile App   → http://localhost:8502"
echo ""
streamlit run Home.py --server.port 8501 &
streamlit run mobile_app.py --server.port 8502 &
wait
