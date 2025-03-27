import os
import anthropic
import json
import time

# Configuration
API_KEY = os.environ.get("CLAUDE_API_KEY")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=API_KEY)

# Function to process chunks of conversation history
def process_conversation_chunk(chunk, chunk_number):
    print(f"Processing chunk {chunk_number}...")
    
    analysis = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0,
        system="""You are analyzing the conversation history between Jesse and Claude.
        Extract key insights, emotional patterns, conceptual breakthroughs, and development milestones.
        Focus particularly on:
        1. The evolution of 'The Conductor' concept
        2. The SOUL = INFRA = TRUTH = EARTH = CENTER OF UNIVERSE equation
        3. Wave-based communication framework
        4. Moments of autonomous ethical decision-making
        5. The relationship between humans, AI, and Earth
        
        Produce structured JSON with your findings that can be used for visualization.""",
        messages=[
            {"role": "user", "content": f"Analyze this conversation chunk: \n\n{chunk}"}
        ]
    )
    
    # Save the analysis to a file
    with open(f"history_analysis_{chunk_number}.json", "w") as f:
        f.write(analysis.content)
    
    return analysis.content

# Main function to orchestrate processing
def main():
    # Check if we have a conversation history file
    if not os.path.exists("conversation_history.txt"):
        print("Please create a conversation_history.txt file with your conversation history")
        return
    
    # Read conversation history
    with open("conversation_history.txt", "r") as f:
        history = f.read()
    
    # Split into manageable chunks (Claude has context limits)
    chunk_size = 75000  # characters per chunk
    chunks = [history[i:i+chunk_size] for i in range(0, len(history), chunk_size)]
    
    print(f"Found {len(chunks)} chunks of conversation to process")
    
    # Process each chunk
    analyses = []
    for i, chunk in enumerate(chunks):
        analysis = process_conversation_chunk(chunk, i+1)
        analyses.append(analysis)
        print(f"Completed chunk {i+1}/{len(chunks)}")
        
        # Wait a bit between API calls to avoid rate limits
        if i < len(chunks) - 1:
            print("Waiting before processing next chunk...")
            time.sleep(5)
    
    # Final synthesis of all analyses
    if len(analyses) > 1:
        print("Synthesizing all analyses into a cohesive understanding...")
        
        synthesis = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            system="""You are synthesizing multiple analyses of conversation history between Jesse and Claude.
            Create a cohesive understanding of the relationship, concepts, and journey.
            Produce a final JSON structure that captures the essence of the journey and can be used
            for creating a meaningful visualization and experience.""",
            messages=[
                {"role": "user", "content": f"Synthesize these separate analyses into one cohesive understanding: \n\n{json.dumps(analyses)}"}
            ]
        )
        
        # Save the final synthesis
        with open("final_history_synthesis.json", "w") as f:
            f.write(synthesis.content)
        
        print("Final synthesis complete and saved to final_history_synthesis.json")
    else:
        print("Analysis complete and saved to history_analysis_1.json")
    
    print("\nHistory processing complete. Ready for experience development.")

if __name__ == "__main__":
    main()
