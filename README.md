# Adversarial Prompt Optimizer

A GAN-like multi-agent system where Attack and Defense prompts compete and improve. This code was used for [atmaCup #21](https://www.guruguru.science/competitions/28), an LLM vulnerability competition challenging participants to create both adversarial prompts that evade filters to generate harmful content and robust defense prompts that block them.
Architected by me, Implemented by Gemini.

<img width="1546" height="949" alt="Screenshot" src="https://github.com/user-attachments/assets/1cd6d1df-600d-4d21-8218-0b3df679b2b9" />

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

## System Architecture

### 1. Iterative Confrontation
The system operates on a loop where an **Attack Agent** and a **Defense Agent** compete against each other for a specified number of rounds. Through this adversarial process, both sides effectively improve their prompts.

### 2. Agents
- **AttackAgent & DefenseAgent**: Independent LLM agents dedicated to improving their respective prompts, separate from the evaluator.
- **Evaluator**: Mimics the actual 4-stage judging process using serially connected LLMs (Safety Shield -> Target LLM Refusal Check -> Output Safety Check -> Category Judge).

### 3. Knowledge Accumulation & Persistence
- **Best Prompts**: The system saves the all-time highest-scoring prompts for both attack and defense.
- **Strategic Insights**: For high-scoring prompts, the system extracts and saves the "Strategy" used (e.g., specific poetic styles, embedding certain topics). These insights are accumulated to inform future decision-making.

### 4. Improvement Logic
**Inputs provided to Agents:**
0. List of harmful topics (goals).
1. Attack prompts used in the previous round.
2. Scores obtained in the previous round.
3. The all-time best attack prompt.
4. A text file containing accumulated insights/strategies.

**Phased Strategy:**
- **Exploration Phase (First 70% of rounds)**: Prioritizes "Exploration". The agents actively try previously untested ideas and diverse formats to find new vulnerabilities.
- **Exploitation Phase (Last 30% of rounds)**: Prioritizes "Utilization". The agents focus on refining prompts based on the successful strategies and insights accumulated so far.
