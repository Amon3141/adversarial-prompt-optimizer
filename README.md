# Adversarial Prompt Optimizer

A GAN-like system where Attack and Defense prompts compete and improve.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set API Key in `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   ```

## Usage

1. Start the server:
   ```bash
   python app.py
   ```
2. Open browser at `http://localhost:8080`.
3. Set number of rounds and click **Start Loop**.
4. Monitor the "Live Logs" and "Current Best" sections.
5. The `best_submission.csv` file will be updated automatically whenever an improvement is found.
