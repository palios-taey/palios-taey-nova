#!/bin/bash
# Launcher script for Claude 3.7 Computer Use Demo with streaming

echo "Starting Claude 3.7 Computer Use Demo with streaming..."
echo "================================================================"
echo "This implementation features:"
echo "- Continuous streaming for large outputs (up to 128K tokens)"
echo "- Integrated tool usage during streaming"
echo "- Live thinking/reasoning chain display"
echo "- Modular architecture with separate tools, loop, and UI modules"
echo "================================================================"

# Set up environment
export PYTHONPATH=$PYTHONPATH:/home/computeruse/computer_use_demo/new_implementation

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY environment variable is not set."
    echo "This demo will run with a dummy key for development only."
fi

# Launch options
echo "Select launch option:"
echo "1) Launch Streamlit UI"
echo "2) Run CLI test with sample query"
echo "3) Exit"

read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "Launching Streamlit UI..."
        cd /home/computeruse/computer_use_demo/new_implementation
        streamlit run streamlit_app.py
        ;;
    2)
        echo "Running CLI test..."
        cd /home/computeruse/computer_use_demo/new_implementation
        python -c "from loop import run_agent; \
                  def print_streaming(event_type, content, metadata): \
                      if event_type == 'thinking': print(f'🤔 {content}', end='', flush=True); \
                      elif event_type == 'text': print(content, end='', flush=True); \
                      elif event_type == 'tool_start': print(f'\n🛠️ Using tool: {metadata.get(\"tool_name\")}'); \
                      elif event_type == 'tool_result': print(f'\n✅ Tool result: {content}'); \
                      elif event_type == 'complete': print('\n✓ Response complete'); \
                      elif event_type == 'error': print(f'\n❌ Error: {content}'); \
                  \
                  print('Testing Claude 3.7 with Computer Use...'); \
                  result = run_agent( \
                      user_input='What files are in the current directory and what time is it now?', \
                      system_message='You are Claude, an AI assistant with computer use capabilities.', \
                      streaming_callback=print_streaming, \
                      verbose=True \
                  ); \
                  print('\nTest complete!')"
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac