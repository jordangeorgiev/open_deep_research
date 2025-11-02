"""Test the local Open Deep Research setup."""
import asyncio
from open_deep_research.deep_researcher import deep_researcher
from langchain_core.messages import HumanMessage

async def test_research():
    """Run a simple test research query."""

    # Simple research query
    query = "What are the latest advances in quantum computing?"

    print(f"\n[TEST] Testing Open Deep Research with query:")
    print(f"   '{query}'")
    print(f"\n{'='*60}")

    # Create config with local settings
    config = {
        "configurable": {
            "summarization_model": "ollama:llama3.2:latest",
            "research_model": "ollama:llama3.2:latest",
            "compression_model": "ollama:llama3.2:latest",
            "final_report_model": "ollama:llama3.2:latest",
            "search_api": "searxng",
            "searxng_url": "http://localhost:8080",
            "max_concurrent_research_units": 2,
            "allow_clarification": False,  # Skip clarification for test
        }
    }

    # Run the research
    inputs = {"messages": [HumanMessage(content=query)]}

    print("\n[START] Starting research...\n")

    try:
        final_state = None
        async for event in deep_researcher.astream(inputs, config=config):
            # Print progress
            for node_name, node_output in event.items():
                print(f"[NODE] {node_name}")
                if node_output and isinstance(node_output, dict) and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, "content"):
                            print(f"   {msg.content[:200]}...")
                print()

                # Capture final state
                final_state = node_output

        print(f"\n{'='*60}")
        print("[SUCCESS] Research completed successfully!")

        # Save final report to file
        if final_state and isinstance(final_state, dict):
            final_report = final_state.get("final_report")
            if final_report:
                # Create output directory if it doesn't exist
                import os
                output_dir = "research_output"
                os.makedirs(output_dir, exist_ok=True)

                # Generate filename with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{output_dir}/research_report_{timestamp}.md"

                # Save report
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(final_report)

                print(f"\n[SAVED] Final report saved to: {filename}")
                print(f"[SIZE] Report length: {len(final_report)} characters")
            else:
                print("\n[WARNING] No final_report found in final state")

        return final_state

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING LOCAL OPEN DEEP RESEARCH")
    print("="*60)
    print("\nConfiguration:")
    print("   - LLM: Ollama (llama3.2:latest)")
    print("   - Search: SearXNG (localhost:8080)")
    print("   - Database: PostgreSQL (localhost:5432)")
    print()

    # Run the test
    asyncio.run(test_research())
