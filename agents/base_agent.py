class BaseAgent:
    def __init__(self, client):
        """
        Initializes the agent with an LLM client.
        
        Args:
            client (LLMClient): The LLM client to use for model interaction.
        """
        self.client = client

    def run(self, task: str) -> str:
        """
        Executes the agent's logic for a given task.
        
        Args:
            task (str): The task or prompt describing what the agent should do.
            
        Returns:
            str: The final result or response from the agent.
        """
        raise NotImplementedError("Each agent must implement the run method.")
