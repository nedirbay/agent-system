import sys
import argparse
import logging
from llm_client import LLMClient
from router import Router

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent System with routing and FileAgent.")
    parser.add_argument("task", nargs="?", type=str, help="The task for the agent system to perform.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Initialize client and router
    client = LLMClient()
    router = Router(client)

    if args.task:
        # Run one-off task
        task = args.task
        logging.info(f"Received single-task request: {task}")
        agent_name, agent = router.route(task)
        logging.info(f"Routing to agent: {agent_name}")
        
        result = agent.run(task)
        print(f"\n[Jogap]:\n{result}\n")
    else:
        # Interactive CLI loop
        print("\n================================================")
        print("        Agent Ulgamyna Hoş Geldiňiz!")
        print("================================================")
        print("Gurallary ulanmak we umumy soraglara jogap bermek üçin")
        print("islendik talaby ýazyň. Çykmak üçin 'exit' ýazyň.\n")
        
        while True:
            try:
                task = input("Siz: ").strip()
                if not task:
                    continue
                if task.lower() in ["exit", "quit", "çyk"]:
                    print("Sag boluň!")
                    break
                
                print("\n[Ulgam] Talap ugrukdyrylýar...")
                agent_name, agent = router.route(task)
                print(f"[Ulgam] Saýlanan agent: {agent_name}")
                print("[Ulgam] Agent işe girizildi...\n")
                
                result = agent.run(task)
                print(f"\n[Jogap]:\n{result}\n")
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\nSag boluň!")
                break
            except Exception as e:
                print(f"\n[Ýalňyşlyk]: {e}\n")

if __name__ == "__main__":
    main()
