class Amygdala:
    def process_input(self, input_data):
        print(f"[Amygdala] Processing input: {input_data}")
        emotion = "fear" if "danger" in input_data.lower() else "neutral"
        return {"emotion": emotion}

    def generate_output(self, emotion):
        return f"Emotional state: {emotion}"

class Hippocampus:
    def __init__(self):
        self.memory = []

    def process_input(self, input_data):
        print(f"[Hippocampus] Storing memory: {input_data}")
        self.memory.append(input_data)
        return {"context": "recent_memory_retrieved"}

    def generate_output(self, context):
        return f"Context: {context}"

class PrefrontalCortex:
    def process_input(self, emotion, context):
        print(f"[Prefrontal Cortex] Deciding based on {emotion} and {context}")
        if emotion == "fear":
            return "flee"
        return "explore"

    def generate_output(self, decision):
        return f"Decision: {decision}"

class BasalGanglia:
    def process_input(self, decision):
        print(f"[Basal Ganglia] Selecting action for: {decision}")
        return f"execute_{decision}"

    def generate_output(self, action):
        return f"Action: {action}"

class Cerebellum:
    def process_input(self, action):
        print(f"[Cerebellum] Refining motor control for: {action}")
        return f"{action}_smoothly"

    def generate_output(self, refined_action):
        return f"Final Motor Output: {refined_action}"

class BrainSystem:
    def __init__(self):
        self.amygdala = Amygdala()
        self.hippocampus = Hippocampus()
        self.prefrontal_cortex = PrefrontalCortex()
        self.basal_ganglia = BasalGanglia()
        self.cerebellum = Cerebellum()

    def run(self, input_data):
        print(f"\n>>> Input received: {input_data}")
        
        # 1. Emotional and Memory processing
        emotion_res = self.amygdala.process_input(input_data)
        memory_res = self.hippocampus.process_input(input_data)
        
        # 2. Decision making (Prefrontal Cortex)
        decision = self.prefrontal_cortex.process_input(emotion_res['emotion'], memory_res['context'])
        
        # 3. Action selection (Basal Ganglia)
        action = self.basal_ganglia.process_input(decision)
        
        # 4. Coordination (Cerebellum)
        refined_action = self.cerebellum.process_input(action)
        
        # 5. Final Output
        final_output = self.cerebellum.generate_output(refined_action)
        
        print(f">>> Result: {final_output}")
        return final_output

if __name__ == "__main__":
    brain = BrainSystem()
    
    # Scenario 1: Danger
    brain.run("A snake is approaching!")
    
    # Scenario 2: Neutral
    brain.run("A sunny day.")
