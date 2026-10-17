from base_agent import BaseAgent

class GeneralAgent(BaseAgent):
    def __init__(self, client):
        super().__init__(client)

    def run(self, task: str) -> str:
        """
        Runs the conversational general agent.
        
        Args:
            task (str): The user's input request/question.
            
        Returns:
            str: LLM response in Turkmen.
        """
        system_prompt = """Sen agent ulgamyndaky GeneralAgent (Umumy kömekçi agent).
Seniň wezipäň ulanyjynyň umumy sowallaryna, gürrüňlerine ýa-de maglumat soramalaryna jogap bermek.
Sen faýllar bilen göni işläp bilmeýärsiň, ýöne faýl amallaryndan başga islendik soraga sypaýy jogap bermelisiň.

Möhüm düzgünler:
1. Jogabyňy elmydama Turkmen dilinde ber.
2. Düşnükli we peýdaly maglumat ber.
"""
        messages = [{"role": "user", "content": task}]
        return self.client.chat(messages, system_prompt=system_prompt)
