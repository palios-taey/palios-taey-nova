#!/usr/bin/env python3
"""
Main entry point for the Claude Custom Agent.
Provides options to run in CLI mode or launch the Streamlit UI.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Ensure parent directory is in path
current_dir = Path(__file__).parent.absolute()
sys.path.append(str(current_dir))

def run_cli():
    """Run the agent in CLI mode"""
    from agent_loop import main as agent_main
    
    try:
        asyncio.run(agent_main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")

def run_ui():
    """Run the Streamlit UI"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("Starting Streamlit UI...")
        
        # Get the path to the UI script
        ui_path = current_dir / "ui.py"
        
        # Launch Streamlit
        os.system(f"streamlit run {ui_path}")
    except ImportError:
        print("Streamlit is not installed. Install with: pip install streamlit")
        print("Then run: python main.py --ui")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude Custom Agent")
    parser.add_argument("--ui", action="store_true", help="Launch the Streamlit UI")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    
    args = parser.parse_args()
    
    # Default to CLI if no arguments provided
    if not args.ui and not args.cli:
        args.cli = True
    
    if args.ui:
        run_ui()
    elif args.cli:
        run_cli()

if __name__ == "__main__":
    main()