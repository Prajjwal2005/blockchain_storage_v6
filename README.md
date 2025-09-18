# blockchain_storage_v6
Blockchain Project by Prajjwal
# decentralized_storage_v5 — Starter


## Setup (backend)


1. Open a terminal in `decentralized_storage_v4/backend`.
2. Create a virtual environment and activate it (recommended):
- Python 3.10+ recommended
- `python -m venv .venv` then activate (`source .venv/bin/activate` on Mac/Linux or `.\.venv\Scripts\activate` on Windows)
3. Install dependencies:
- `pip install -r requirements.txt`
4. Start the Flask app:
- `python app.py`
5. Open `http://localhost:5000/` in your browser. The frontend is served by Flask.


Files uploaded will be stored in `backend/storage/` and the blockchain is saved to `backend/storage/chain.json`.


## Notes
- This is a minimal educational starter. In production you'd want:
- Authentication and authorization (WebAuthn/JWT etc.)
- Safe handling of file types and size limits
- Robust blockchain consensus and signature scheme
- Proper logging, monitoring, and backup
