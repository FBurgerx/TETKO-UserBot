#!/data/data/com.termux/files/usr/bin/bash
cd ~/TETKO_developing
export TETKO_API_ID=$(python3 -c "import json; print(json.load(open('config.json'))['api_id'])")
export TETKO_API_HASH=$(python3 -c "import json; print(json.load(open('config.json'))['api_hash'])")
export TETKO_SESSION=$(python3 -c "import json; print(json.load(open('config.json')).get('session_name', 'tetko'))")
exec python run_tetko.py
