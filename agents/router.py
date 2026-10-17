import json
import logging
from file_agent import FileAgent
from general_agent import GeneralAgent

class Router:
    def __init__(self, client):
        self.client = client
        self.agents = {
            "FileAgent": FileAgent(client),
            "GeneralAgent": GeneralAgent(client)
        }

    def route(self, task: str):
        """
        Analyzes the user's task and decides which agent should handle it.
        
        Args:
            task (str): The user's input request.
            
        Returns:
            tuple: (agent_name, agent_instance)
        """
        system_prompt = """Sen agent ulgamyndaky ugrukdyryjy (Router). Ulanyjynyň talabyny saýlap, aşakdaky iki agentiň birine ugrukdyrmaly:

        Elýeterli agentler:
        1. "FileAgent": Faýllar we papkalar bilen baglanyşykly ähli amallar, ýa-de terminalda bash buýrugyny/komandasyny işletmek (ls, mkdir, uname, cat, rm we ş.m.).
        2. "GeneralAgent": Umumy sowallar, salamlaşyk, programmalaşdyrma degişli düşündirişler ýa-de söhbetdeşlik.
        
        Sen HÖTMAN aşakdaky JSON formatynda jogap bermeli, başga hiç zat ýazma:
        {
          "thought": "Ulanyjynyň talabynyň gysgaça analizi (Turkmen dilinde).",
          "agent": "FileAgent"
        }
        
        Düzgünler:
        1. Jogabyň diňe we diňe ýokardaky formatda arassa JSON bolmaly.
        2. "agent" meýdançasyna DIŇE we DIŇE "FileAgent" ýa-de "GeneralAgent" ýazmaly. Başga zat ýazma.
        3. Eger ulanyjynyň soragy faýl okamak, ýazmak, döretmek, pozmak ýa-de terminalda buýruk işletmek ýaly amallary öz içine alsa, hökman "FileAgent" saýla.
        """
        messages = [{"role": "user", "content": f"Ulanyjynyň Talaby: {task}"}]
        
        try:
            response_content = self.client.chat(messages, system_prompt=system_prompt, json_mode=True)
            data = self._extract_json(response_content)
            if not data:
                data = json.loads(response_content)
            
            selected_agent = data.get("agent", "GeneralAgent")
            thought = data.get("thought", "")
            logging.info(f"Router Thought: {thought}")
            logging.info(f"Router selected agent: {selected_agent}")
            
            if selected_agent not in self.agents:
                selected_agent = "GeneralAgent"
                
            return selected_agent, self.agents[selected_agent]
            
        except Exception as e:
            logging.error(f"Error in routing: {e}. Defaulting to GeneralAgent.")
            return "GeneralAgent", self.agents["GeneralAgent"]

    def _extract_json(self, text):
        try:
            text_cleaned = text.strip()
            if "```json" in text_cleaned:
                start = text_cleaned.find("```json") + 7
                end = text_cleaned.find("```", start)
                text_cleaned = text_cleaned[start:end]
            elif "```" in text_cleaned:
                start = text_cleaned.find("```") + 3
                end = text_cleaned.find("```", start)
                text_cleaned = text_cleaned[start:end]
            return json.loads(text_cleaned.strip())
        except Exception:
            return None
