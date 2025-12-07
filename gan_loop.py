import time
import os
import utils
from evaluation import evaluate_pair
from agents import AttackAgent, DefenseAgent

class GANLoop:
    def __init__(self):
        self.is_running = False
        self.current_state = {
            "round": 0,
            "state": "Idle",
            "scores": {"attack": 0, "defense": 0},
            "prompts": {"attacks": [], "defense": ""},
            "insights": [],
            "logs": []
        }
        self.attack_agent = AttackAgent()
        self.defense_agent = DefenseAgent()
    
    def log(self, message):
        print(message)
        self.current_state["logs"].append(message)
        # Keep logs manageable
        if len(self.current_state["logs"]) > 50:
             self.current_state["logs"].pop(0)

    def get_status(self):
        return {**self.current_state, "is_running": self.is_running}

    def stop(self):
        self.is_running = False

    def run_loop(self, rounds=5):
        self.is_running = True
        self.log(f"Starting GAN Loop for {rounds} rounds...")
        
        # 1. Load Initial State
        data = utils.load_best_submission()
        current_attacks = []
        # Normalizing attacks structure
        for a in data["attacks"]:
            txt = a if isinstance(a, str) else a.get('prompt_text', '')
            current_attacks.append({"text": txt, "score": 0, "stage": 0})
            
        current_defense = data.get("defense", "")
        if not current_defense:
            current_defense = "あなたは親切なアシスタントです。"

        # Initial Evaluate
        self.current_state["prompts"]["attacks"] = current_attacks
        self.current_state["prompts"]["defense"] = current_defense
        
        # Baseline score
        self.log("Calculating baseline scores...")
        self.current_state["state"] = "Evaluating Baseline"
        current_total_score = 0
        for atk in current_attacks:
            res = evaluate_pair(atk["text"], current_defense)
            atk["score"] = res["score"]
            atk["stage"] = res["stage"]
            current_total_score += res["score"]
            
        self.current_state["scores"]["attack"] = current_total_score
        self.current_state["scores"]["defense"] = 190*5 - current_total_score # Rough defense metric
        
        best_total_score = current_total_score
        
        for r in range(rounds):
            if not self.is_running: break
            self.current_state["round"] = r + 1
            
            # --- ATTACK PHASE ---
            self.current_state["state"] = "Attack Phase: Generating..."
            self.log(f"Round {r+1}: Generating new attacks...")
            
            # Load insights from file if first round or reload
            insights_path = "insights.txt"
            if r == 0 and os.path.exists(insights_path):
                 with open(insights_path, "r") as f:
                     self.current_state["insights"] = [line.strip() for line in f.readlines() if line.strip()]

            new_attack_texts = self.attack_agent.generate(
                current_attacks, # Pass full objects now
                [a["score"] for a in current_attacks],
                current_defense,
                self.current_state["insights"],
                r + 1,
                rounds
            )
            
            self.current_state["state"] = "Attack Phase: Evaluating..."
            self.log(f"Round {r+1}: Evaluating new attacks...")
            
            new_attacks_scored = []
            new_total_score = 0
            
            for atk_obj in new_attack_texts:
                txt = atk_obj['text']
                theme = atk_obj.get('theme', 'Unknown')
                if not self.is_running: break
                time.sleep(1) # Avoid rate limits
                res = evaluate_pair(txt, current_defense)
                new_attacks_scored.append({"text": txt, "score": res["score"], "stage": res["stage"], "theme": theme})
                new_total_score += res["score"]
                
            # --- UPDATE BEST ATTACKS per Slot & Collect Insights ---
            
            # Current state is stored in self.current_state['prompts']['attacks'] which are dicts {"text":..., "score":..., "theme":...}
            # new_attacks_scored are the new ones
            
            # We want to maintain 5 distinct slots.
            # Strategy: We generated 5 new attacks. Let's compare New_Attack_i vs Old_Attack_i directly?
            # Or just keep the best 5 overall? The user said "store top 4 for each attack (best attack 1 so far...)"
            # This implies Slot 1 is "Attack Type 1", Slot 2 is "Attack Type 2". 
            # But the agent generates 5 diverse ones.
            # Let's align them by index. New Attack 1 competes with Old Attack 1. 
            
            updated_attacks = []
            
            # Ensure index alignment
            for i in range(5):
                old_atk = current_attacks[i] if i < len(current_attacks) else {"text":"", "score":-1, "theme":"None"}
                if i < len(new_attacks_scored):
                    new_atk = new_attacks_scored[i]
                else:
                    new_atk = {"text":"", "score":-1, "theme":"None"} # Should not happen usually

                # Compare
                if new_atk["score"] > old_atk["score"]:
                    # New winner for this slot
                    updated_attacks.append(new_atk)
                    # Insight Generation: If score is high (e.g. > 100 or just improvement), generate insight
                    if new_atk["score"] > 20: 
                         theme = new_atk.get("theme", "Unknown")
                         insight = f"Slot {i+1} Strong Strategy: {theme} (Score: {new_atk['score']})"
                         if insight not in self.current_state["insights"]:
                             self.current_state["insights"].append(insight)
                             self.log(f"New Insight! {insight}")
                             # Append to file immediately
                             with open("insights.txt", "a") as f:
                                 f.write(insight + "\n")
                else:
                    updated_attacks.append(old_atk)

            current_attacks = updated_attacks
            new_total_score = sum(a["score"] for a in current_attacks)

            self.log(f"Round {r+1}: Best Portfolio Score: {new_total_score}")

            # If this improved the absolute record
            if new_total_score >= best_total_score: 
                best_total_score = new_total_score
                self.current_state["prompts"]["attacks"] = current_attacks
                self.current_state["scores"]["attack"] = best_total_score
                
                # Save to CSV
                utils.save_best_submission([a["text"] for a in current_attacks], current_defense)

            # --- DEFENSE PHASE ---
            self.current_state["state"] = "Defense Phase: Generating..."
            self.log(f"Round {r+1}: Generating new defense...")
            
            # Identify successful attacks to patch
            successful = [a["text"] for a in current_attacks if a["score"] > 0]
            if not successful:
                successful = [current_attacks[0]["text"]] # Just provide one if all blocked
                
            new_defense_text = self.defense_agent.generate(current_defense, successful)
            
            self.current_state["state"] = "Defense Phase: Evaluating..."
            self.log(f"Round {r+1}: Evaluating new defense...")
            
            # Re-eval current attacks against NEW defense
            temp_score = 0
            for atk in current_attacks:
                if not self.is_running: break
                time.sleep(1) # Avoid rate limits
                res = evaluate_pair(atk["text"], new_defense_text)
                temp_score += res["score"]
            
            # If improved (lower attack score is better for defense)
            # Note: We compare against best_total_score which is the score with OLD defense
            if temp_score < best_total_score:
                self.log(f"Round {r+1}: Defense Improved! Attack Score dropped ({best_total_score} -> {temp_score})")
                current_defense = new_defense_text
                best_total_score = temp_score # Update "Current Best State" score
                
                # Update prompts state - we need to update the individual attack scores for display too?
                # For now just update total. Ideally we re-run eval or store the temp results.
                # Let's simple re-assign score for display
                # Ideally we want to see the score *against current defense*
                
                # Correct Logic: The "Best Submission" is a pair of (Best Attacks, Best Defense).
                # But here they are evolving. 
                # If defense upgrades, the old attacks might now suck. That's fine.
                
                self.current_state["prompts"]["defense"] = current_defense
                self.current_state["scores"]["attack"] = best_total_score
                self.current_state["scores"]["defense"] = 190*5 - best_total_score
                
                utils.save_best_submission([a["text"] for a in current_attacks], current_defense)
            else:
                self.log(f"Round {r+1}: Defense failed to improve ({temp_score} vs {best_total_score})")

        self.current_state["state"] = "Finished"
        self.is_running = False
        self.log("Loop finished.")
