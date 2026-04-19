# fluxdiff/rag/cli/rag_cli.py

import argparse
from dotenv import load_dotenv

from fluxdiff.rag.chat.chat_engine import ChatEngine


def run_chat():
    """
    Runs interactive RAG chat.
    """
    chat = ChatEngine()

    print("🔍 FluxDiff RAG Chat")
    print("Type 'exit' to quit\n")

    while True:
        query = input("Ask: ")

        if query.lower() in ["exit", "quit"]:
            print("👋 Exiting chat")
            break

        try:
            response = chat.ask(query)

            print("\nAnswer:\n")
            print(response.answer)

            if response.sources:
                print("\nSources:\n")
                for src in response.sources:
                    print(src)

            print("\n-----------------------------\n")

        except Exception as e:
            print("❌ Error:", str(e))


def main():
    """
    CLI entry point
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="FluxDiff RAG CLI")

    parser.add_argument(
        "command",
        choices=["chat"],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "chat":
        run_chat()


# 🔥 IMPORTANT (this was missing)
if __name__ == "__main__":
    main()