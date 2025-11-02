"""Example: Quantum Computing Error Correction Research

This example demonstrates using local Ollama models to research
quantum computing error correction techniques and their practical applications.
"""
import asyncio
import os
from datetime import datetime
from open_deep_research.deep_researcher import deep_researcher
from langchain_core.messages import HumanMessage


async def run_quantum_research():
    """Run quantum computing error correction research."""

    query = """What are the most promising quantum error correction techniques
    currently being developed, and how do they compare in terms of practical
    implementation challenges and performance?"""

    print("\n" + "="*70)
    print("QUANTUM COMPUTING ERROR CORRECTION RESEARCH")
    print("="*70)
    print(f"\nQuery: {query}")
    print("\nConfiguration:")
    print("   - LLM: Ollama (llama3.2:latest)")
    print("   - Search: SearXNG (localhost:8080)")
    print("   - Database: PostgreSQL (localhost:5432)")
    print("\n" + "="*70 + "\n")

    # Configure for local Ollama research
    config = {
        "configurable": {
            "summarization_model": "ollama:llama3.2:latest",
            "research_model": "ollama:llama3.2:latest",
            "compression_model": "ollama:llama3.2:latest",
            "final_report_model": "ollama:llama3.2:latest",
            "search_api": "searxng",
            "searxng_url": "http://localhost:8080",
            "max_concurrent_research_units": 2,
            "allow_clarification": False,
        }
    }

    inputs = {"messages": [HumanMessage(content=query)]}

    try:
        print("[START] Starting research...\n")
        final_state = None

        async for event in deep_researcher.astream(inputs, config=config):
            for node_name, node_output in event.items():
                print(f"[NODE] {node_name}")
                if node_output and isinstance(node_output, dict) and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, "content"):
                            content_preview = msg.content[:150].replace("\n", " ")
                            # Handle Unicode characters for Windows console
                            try:
                                print(f"   {content_preview}...")
                            except UnicodeEncodeError:
                                safe_preview = content_preview.encode('ascii', errors='replace').decode('ascii')
                                print(f"   {safe_preview}...")
                print()
                final_state = node_output

        print("="*70)
        print("[SUCCESS] Research completed successfully!")

        # Save final report
        if final_state and isinstance(final_state, dict):
            final_report = final_state.get("final_report")
            if final_report:
                # Ensure output directory exists
                output_dir = "examples/local_ollama_examples/reports"
                os.makedirs(output_dir, exist_ok=True)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{output_dir}/quantum_error_correction_{timestamp}.md"

                # Save report
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# Quantum Error Correction Research Report\n\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**Query:** {query}\n\n")
                    f.write("---\n\n")
                    f.write(final_report)

                print(f"\n[SAVED] Research report saved to: {filename}")
                print(f"[SIZE] Report length: {len(final_report)} characters")
                print(f"[LINES] Report lines: {final_report.count(chr(10)) + 1}")
            else:
                print("\n[WARNING] No final_report found in final state")

        return final_state

    except Exception as e:
        print(f"\n[ERROR] Research failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LOCAL OLLAMA RESEARCH EXAMPLE: QUANTUM COMPUTING")
    print("="*70)

    # Run the research
    result = asyncio.run(run_quantum_research())

    if result:
        print("\n" + "="*70)
        print("RESEARCH COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nCheck examples/local_ollama_examples/reports/ for the generated report.")
    else:
        print("\n" + "="*70)
        print("RESEARCH FAILED")
        print("="*70)
