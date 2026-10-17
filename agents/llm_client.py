import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class LLMClient:
    def __init__(self, base_url="http://172.16.6.80:8084", model="gemma4:26b"):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"
        self.model = model

    def chat(self, messages, system_prompt=None, json_mode=False):
        """
        Sends a list of messages to the LLM.
        
        Args:
            messages (list): A list of dicts with 'role' and 'content' keys.
            system_prompt (str, optional): A system prompt to prepend/set.
            json_mode (bool): If True, forces the output to be JSON.
            
        Returns:
            str: The assistant response content.
        """
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        
        # Append other messages
        payload_messages.extend(messages)
        
        payload = {
            "model": self.model,
            "messages": payload_messages,
            "stream": False
        }
        
        if json_mode:
            payload["format"] = "json"
            
        try:
            logging.debug(f"Sending payload to LLM: {json.dumps(payload, indent=2)}")
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            logging.debug(f"LLM Response: {json.dumps(result, indent=2)}")
            
            # Extract content
            message = result.get("message", {})
            content = message.get("content", "")
            return content.strip()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with LLM server: {e}")
            raise RuntimeError(f"LLM API request failed: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response from LLM server: {e}")
            raise RuntimeError(f"Invalid JSON response from LLM server: {e}")

if __name__ == "__main__":
    # Quick verification
    client = LLMClient()
    print("Testing standard chat...")
    resp = client.chat([{"role": "user", "content": "Tell me a 1-word greeting in Turkmen."}])
    print("Response:", resp)
    
    print("\nTesting JSON chat...")
    resp_json = client.chat(
        [{"role": "user", "content": "Respond with a JSON object: {'greeting': 'Turkmen greeting'}"}],
        json_mode=True
    )
    print("JSON Response:", resp_json)
