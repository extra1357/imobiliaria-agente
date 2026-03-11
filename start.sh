#!/bin/bash
cd ~/agentes
source venv/bin/activate
uvicorn api:app --reload
