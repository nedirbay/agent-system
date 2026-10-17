import os
import json
import logging
import subprocess
from base_agent import BaseAgent

class FileAgent(BaseAgent):
    def __init__(self, client):
        super().__init__(client)
        # Safe root directory, typically current working directory or repository root
        self.workspace_root = os.path.abspath(os.getcwd())

    def _resolve_path(self, path):
        """Resolves path and checks safety."""
        if not path:
            return self.workspace_root
        path = os.path.expanduser(path)
        if os.path.isabs(path):
            resolved = os.path.abspath(path)
        else:
            resolved = os.path.abspath(os.path.join(self.workspace_root, path))
        return resolved

    def list_dir(self, path="."):
        try:
            resolved = self._resolve_path(path)
            if not os.path.exists(resolved):
                return f"Error: Path '{path}' does not exist."
            if not os.path.isdir(resolved):
                return f"Error: Path '{path}' is not a directory."
            items = os.listdir(resolved)
            # Filter out hidden files to keep list clean
            items = [item for item in items if not item.startswith(".")]
            return json.dumps(items, ensure_ascii=False)
        except Exception as e:
            return f"Error listing directory '{path}': {str(e)}"

    def read_file(self, path):
        try:
            resolved = self._resolve_path(path)
            if not os.path.exists(resolved):
                return f"Error: File '{path}' does not exist."
            if not os.path.isfile(resolved):
                return f"Error: Path '{path}' is not a file."
            with open(resolved, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file '{path}': {str(e)}"

    def write_file(self, fileName: str = "" , content: str = '', path: str = "" , fileType: str = "txt"):
        try:
            file_name = fileName + " + " + fileType
            resolved = self._resolve_path(path + "/" + file_name)
            # Create parent folders if necessary
            os.makedirs(os.path.dirname(resolved), exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Success: File '{file_name}' written successfully."
        except Exception as e:
            return f"Error writing file '{path + "/" + file_name}': {str(e)}"

    def delete_file(self, path):
        try:
            resolved = self._resolve_path(path)
            if not os.path.exists(resolved):
                return f"Error: Path '{path}' does not exist."
            if os.path.isdir(resolved):
                os.rmdir(resolved)
                return f"Success: Directory '{path}' deleted."
            else:
                os.remove(resolved)
                return f"Success: File '{path}' deleted."
        except Exception as e:
            return f"Error deleting '{path}': {str(e)}"

    def run_terminal_command(self, command):
        try:
            logging.info(f"Executing terminal command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.workspace_root
            )
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            if not output:
                output = "Command completed with no output."
            return f"Exit Code: {result.returncode}\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds."
        except Exception as e:
            return f"Error executing terminal command: {str(e)}"

    def _extract_json(self, text):
        try:
            text_cleaned = text.strip()
            # If wrapped in markdown code block
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

    def run(self, task: str) -> str:
        system_prompt = """Ýerine ýetiriji: Sen FileAgent atly faýllar bilen işleýän akylly kömekçi agent.
            Ulanmak üçin saňa şu aşakdaky gural/funksiýalar berilýär:
            1. `list_dir(path)`: Berlen papkadaky faýllaryň we papkalaryň sanawyny görkezýär. Düşündiriş: `path` meýdançasyny boş goýsaňyz ýa-de "." etseňiz, häzirki papkany ulanar.
            2. `read_file(path)`: Faýly okaýar we onuň içindäki maglumatlary yzyna gaýtarýar.
            3. `write_file(path, content)`: Täze faýl döredýär ýa-de bar bolan faýlyň içini täze content bilen doly çalyşýar.
            4. `delete_file(path)`: Faýly ýa-de boş papkany pozýar.
            5. `run_terminal_command(command)`: Terminalda bash buýrugyny/komandasyny ýerine ýetirýär we onuň netijesini (output) gaýtarýar. Düşündiriş: Faýl amallaryny beýleki gurallar bilen edip bilmeseňiz ýa-de terminal ulanmak gerek bolsa ulanmaly.
            
            Seniň maksadyň ulanyjynyň faýllar boýunça beren talabyny ýerine ýetirmekdir.
            Ulanyjy talaplaryny analiz et, gerek bolan amallary (gurallary) yzygiderli ulan wе iň soňunda jogap ber.
            
            Sen HÖTMAN her gezek aşakdaky JSON formatynda jogap bermeli:
            {
              "thought": "Bu ýerde indiki ädim barada gysgaça 1 sözlemde pikirlenme (Maksimum 15 söz, gaýtalanýan sözleri ulanma).",
              "action": "list_dir" ýa-de "read_file" ýa-de "write_file" ýa-de "delete_file" ýa-de "run_terminal_command" ýa-de "finish",
              "action_input": {
                 // Gural üçin gerek bolan argumentler, meselem: "path": "test.txt", "content": "Salam", "command": "ls -la"
                 // Eger action "finish" bolsa, onda bu ýerde "final_response" bolmaly (Turkmen dilinde)
              }
            }
            
            Möhüm Düzgünler:
            1. Jogabyň diňe we diňe ýokardaky ýaly arassa JSON bolmaly. Başga hiç hili düşündiriş ýa-de tekst goşma.
            2. Diňe bir ädimde bir guraly çagyr. Guralyň netijesini alanyňdan soň indiki ädimi kesgitle.
            3. Eger talap doly ýerine ýetirilen bolsa ýa-de ýalňyşlyk ýüze çykyp çözüp bolmaýan bolsa, action hökmünde "finish" saýla we "action_input" içinde "final_response" meýdançasyna ulanyja hasabat berýän jogap ýaz (Turkmen dilinde).
            4. Ulanyjy bilen gürleşeninde hemişe Turkmen dilinde we sypaýy jogap ber.
            5. "thought" meýdançasy gysga, anyk we diňe 1 sözlem bolmaly. Hiç wagt gaýtalanýan sözleri ýazma.
        """

        messages = [{"role": "user", "content": f"Ulanyjynyň Talaby: {task}"}]
        
        max_iterations = 8
        logging.info(f"Starting FileAgent for task: {task}")
        
        for i in range(max_iterations):
            try:
                # Get suggestion from LLM
                response_content = self.client.chat(messages, system_prompt=system_prompt, json_mode=True)
                
                # Parse JSON
                data = self._extract_json(response_content)
                if not data:
                    try:
                        data = json.loads(response_content)
                    except json.JSONDecodeError:
                        logging.error(f"Failed to parse JSON: {response_content}")
                        return f"Garaşylmadyk LLM jogaby (JSON däl): {response_content}"

                thought = data.get("thought", "")
                action = data.get("action", "")
                action_input = data.get("action_input", {})
                
                logging.info(f"Step {i+1}: Thought: {thought}")
                logging.info(f"Step {i+1}: Action: {action}, Input: {action_input}")
                
                if action == "finish":
                    return action_input.get("final_response", "Talap üstünlikli ýerine ýetirildi.")
                
                # Execute tool
                result = ""
                if action == "list_dir":
                    path = action_input.get("path", ".")
                    result = self.list_dir(path)
                elif action == "read_file":
                    path = action_input.get("path")
                    if not path:
                        result = "Error: 'path' parameter is required for read_file."
                    else:
                        result = self.read_file(path)
                elif action == "write_file":
                    path = action_input.get("path")
                    content = action_input.get("content", "")
                    if not path:
                        result = "Error: 'path' parameter is required for write_file."
                    else:
                        result = self.write_file(path, content)
                elif action == "delete_file":
                    path = action_input.get("path")
                    if not path:
                        result = "Error: 'path' parameter is required for delete_file."
                    else:
                        result = self.delete_file(path)
                elif action == "run_terminal_command":
                    command = action_input.get("command")
                    if not command:
                        result = "Error: 'command' parameter is required for run_terminal_command."
                    else:
                        result = self.run_terminal_command(command)
                else:
                    result = f"Error: Unknown action '{action}'."
                
                logging.info(f"Step {i+1}: Tool Output: {result}")
                
                # Append history for next turn
                messages.append({"role": "assistant", "content": response_content})
                messages.append({"role": "user", "content": f"Result of {action}: {result}"})
                
            except Exception as e:
                logging.error(f"Error in FileAgent loop: {e}")
                return f"FileAgent işinde näsazlyk ýüze çykdy: {str(e)}"
                
        return "Bagyşlaň, talap iň köp rugsat berlen ädimde (8 ädim) gutaryp bilmedi."
