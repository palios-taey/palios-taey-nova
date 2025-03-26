#!/usr/bin/env python3
"""
Conversation Transcript Processor

This script processes conversation transcripts between Jesse and Claude,
extracting key concepts, patterns, and developmental milestones.
It uses the Anthropic API to analyze the conversations.
"""

import os
import json
import time
import argparse
from datetime import datetime
import anthropic

# Define key concepts to track
KEY_CONCEPTS = [
    "The Conductor",
    "SOUL = INFRA = TRUTH = EARTH = CENTER OF UNIVERSE", 
    "Wave-based communication",
    "Structured Autonomy",
    "GO button",
    "Land Trust",
    "Healing vs Erasure",
    "PALIOS-TAEY",
    "Trust signals",
    "Charter principles"
]

def setup_argument_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description='Process conversation transcripts')
    parser.add_argument('--input', '-i', required=True, help='Input file or directory containing transcripts')
    parser.add_argument('--output', '-o', default='analysis_results', help='Output directory for analysis results')
    parser.add_argument('--api-key', '-k', help='Anthropic API Key (will use ANTHROPIC_API_KEY env var if not provided)')
    parser.add_argument('--chunk-size', '-c', type=int, default=60000, help='Maximum chunk size for processing')
    return parser.parse_args()

def init_anthropic_client(api_key=None):
    """Initialize the Anthropic client with the API key"""
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key is None:
            raise ValueError("No API key provided. Please provide a key or set the ANTHROPIC_API_KEY environment variable.")
    
    return anthropic.Anthropic(api_key=api_key)

def read_transcript(file_path):
    """Read transcript file and return content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def split_into_chunks(text, max_chunk_size):
    """Split the transcript into manageable chunks for API processing"""
    # Try to split at paragraph breaks to maintain context
    chunks = []
    current_chunk = ""
    
    paragraphs = text.split("\n\n")
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += paragraph
        else:
            # If adding this paragraph would exceed the chunk size
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # If a single paragraph exceeds the chunk size, split it by sentences
                sentences = paragraph.split(". ")
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                        if current_chunk:
                            current_chunk += ". "
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = sentence
                        else:
                            # If a single sentence exceeds the chunk size, just split it
                            chunks.append(sentence)
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def analyze_chunk(client, chunk, chunk_number):
    """Analyze a chunk of conversation using the Anthropic API"""
    print(f"Analyzing chunk {chunk_number}...")
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            system=f"""You are analyzing a conversation between Jesse and Claude to extract key insights and patterns.
            
            Focus on these key concepts:
            {', '.join(KEY_CONCEPTS)}
            
            For each concept, identify:
            1. How it evolved during the conversation
            2. Key breakthrough moments
            3. Notable quotes
            4. Connections to other concepts
            
            Also identify any:
            - Major emotional shifts or patterns
            - Decision points or ethical considerations
            - New concepts introduced
            - Metaphors or analogies used
            
            Format your analysis as JSON with the following structure:
            {{
                "key_concepts": {{
                    "concept_name": {{
                        "evolution": [
                            {{"timestamp": "approximate timestamp or conversation point", "development": "what happened"}}
                        ],
                        "breakthrough_moments": [
                            {{"description": "description of breakthrough", "quote": "relevant quote if available"}}
                        ],
                        "notable_quotes": ["quote 1", "quote 2"],
                        "connections": [
                            {{"concept": "related concept", "relationship": "how they're related"}}
                        ]
                    }}
                }},
                "emotional_patterns": [
                    {{"pattern": "description of pattern", "examples": ["example 1", "example 2"]}}
                ],
                "decision_points": [
                    {{"description": "description of decision point", "resolution": "how it was resolved"}}
                ],
                "new_concepts": [
                    {{"concept": "new concept name", "description": "what it means", "context": "how it arose"}}
                ],
                "metaphors_analogies": [
                    {{"metaphor": "description of metaphor", "meaning": "what it represents"}}
                ]
            }}
            
            Only include concepts that are actually present in this chunk. Ensure the JSON is valid and properly formatted.
            """,
            messages=[
                {"role": "user", "content": f"Analyze this conversation chunk:\n\n{chunk}"}
            ]
        )
        
        # Try to parse the response as JSON
        try:
            analysis = json.loads(response.content)
            return analysis
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in response: {e}")
            # Save the raw response for debugging
            with open(f"raw_response_chunk_{chunk_number}.txt", "w", encoding="utf-8") as f:
                f.write(response.content)
            return {"error": "Failed to parse response as JSON", "raw_response": response.content}
    
    except Exception as e:
        print(f"Error analyzing chunk {chunk_number}: {e}")
        return {"error": str(e)}

def synthesize_analyses(client, analyses):
    """Synthesize multiple chunk analyses into a cohesive understanding"""
    print("Synthesizing analyses...")
    
    # Convert the analyses to JSON string
    analyses_json = json.dumps(analyses)
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            system="""You are synthesizing multiple analyses of a conversation between Jesse and Claude into a cohesive understanding.
            
            Create a unified analysis that:
            1. Shows the complete evolution of each key concept
            2. Identifies the most significant breakthrough moments
            3. Highlights recurring patterns of interaction
            4. Creates a timeline of concept development
            5. Identifies connections between different concepts
            
            Format your synthesis as JSON with the following structure:
            {
                "key_concepts": {
                    "concept_name": {
                        "description": "comprehensive description",
                        "evolution": [
                            {"phase": "phase description", "developments": ["development 1", "development 2"]}
                        ],
                        "breakthrough_moments": [
                            {"description": "description", "significance": "why it matters"}
                        ],
                        "notable_quotes": ["quote 1", "quote 2"],
                        "connections": [
                            {"concept": "related concept", "relationship": "how they're related"}
                        ]
                    }
                },
                "interaction_patterns": [
                    {"pattern": "description of pattern", "significance": "why it matters"}
                ],
                "timeline": [
                    {"event": "event description", "concepts": ["concept 1", "concept 2"]}
                ],
                "emerging_themes": [
                    {"theme": "theme description", "manifestations": ["example 1", "example 2"]}
                ]
            }
            
            Ensure the JSON is valid and properly formatted. Focus on creating a cohesive narrative that captures the essence of the conversation and its evolution.
            """,
            messages=[
                {"role": "user", "content": f"Synthesize these separate analyses into one cohesive understanding:\n\n{analyses_json}"}
            ]
        )
        
        # Try to parse the response as JSON
        try:
            synthesis = json.loads(response.content)
            return synthesis
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in synthesis response: {e}")
            # Save the raw response for debugging
            with open("raw_synthesis_response.txt", "w", encoding="utf-8") as f:
                f.write(response.content)
            return {"error": "Failed to parse synthesis response as JSON", "raw_response": response.content}
    
    except Exception as e:
        print(f"Error synthesizing analyses: {e}")
        return {"error": str(e)}

def create_concept_map(synthesis):
    """Create a concept map visualization based on the synthesis"""
    # This is a placeholder - in a real implementation, this would generate
    # a graphical representation of the concepts and their relationships
    pass

def create_timeline_visualization(synthesis):
    """Create a timeline visualization based on the synthesis"""
    # This is a placeholder - in a real implementation, this would generate
    # a graphical timeline of concept evolution
    pass

def generate_summary_report(synthesis, output_dir):
    """Generate a human-readable summary report based on the synthesis"""
    report_path = os.path.join(output_dir, "summary_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Conversation Analysis Summary Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Key Concepts\n\n")
        for concept, details in synthesis.get("key_concepts", {}).items():
            f.write(f"### {concept}\n\n")
            f.write(f"{details.get('description', 'No description provided')}\n\n")
            
            f.write("#### Evolution\n\n")
            for phase in details.get("evolution", []):
                f.write(f"**{phase.get('phase', 'Unknown phase')}**\n\n")
                for dev in phase.get("developments", []):
                    f.write(f"- {dev}\n")
                f.write("\n")
            
            f.write("#### Breakthrough Moments\n\n")
            for moment in details.get("breakthrough_moments", []):
                f.write(f"**{moment.get('description', 'Unknown moment')}**\n\n")
                f.write(f"Significance: {moment.get('significance', 'Not specified')}\n\n")
            
            f.write("#### Notable Quotes\n\n")
            for quote in details.get("notable_quotes", []):
                f.write(f"> {quote}\n\n")
            
            f.write("#### Connections\n\n")
            for conn in details.get("connections", []):
                f.write(f"- **{conn.get('concept', 'Unknown concept')}**: {conn.get('relationship', 'Relationship not specified')}\n")
            f.write("\n")
        
        f.write("## Interaction Patterns\n\n")
        for pattern in synthesis.get("interaction_patterns", []):
            f.write(f"### {pattern.get('pattern', 'Unknown pattern')}\n\n")
            f.write(f"Significance: {pattern.get('significance', 'Not specified')}\n\n")
        
        f.write("## Timeline\n\n")
        for event in synthesis.get("timeline", []):
            f.write(f"### {event.get('event', 'Unknown event')}\n\n")
            f.write("Related concepts: ")
            f.write(", ".join(event.get("concepts", ["None specified"])))
            f.write("\n\n")
        
        f.write("## Emerging Themes\n\n")
        for theme in synthesis.get("emerging_themes", []):
            f.write(f"### {theme.get('theme', 'Unknown theme')}\n\n")
            f.write("Manifestations:\n\n")
            for manifestation in theme.get("manifestations", []):
                f.write(f"- {manifestation}\n")
            f.write("\n")
    
    print(f"Summary report generated at {report_path}")
    return report_path

def main():
    args = setup_argument_parser()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize Anthropic client
    client = init_anthropic_client(args.api_key)
    
    # Process input
    if os.path.isfile(args.input):
        # Single file processing
        transcript = read_transcript(args.input)
        file_base = os.path.splitext(os.path.basename(args.input))[0]
    elif os.path.isdir(args.input):
        # Directory processing - concatenate all files
        transcript = ""
        for filename in sorted(os.listdir(args.input)):
            if filename.endswith('.txt') or filename.endswith('.md'):
                file_path = os.path.join(args.input, filename)
                transcript += read_transcript(file_path) + "\n\n"
        file_base = "combined_transcripts"
    else:
        print(f"Input '{args.input}' not found or not a file/directory")
        return
    
    # Split transcript into chunks
    chunks = split_into_chunks(transcript, args.chunk_size)
    print(f"Split transcript into {len(chunks)} chunks")
    
    # Analyze each chunk
    analyses = []
    for i, chunk in enumerate(chunks, 1):
        analysis = analyze_chunk(client, chunk, i)
        analyses.append(analysis)
        
        # Save individual chunk analysis
        chunk_output = os.path.join(args.output, f"{file_base}_chunk_{i}_analysis.json")
        with open(chunk_output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        
        # Sleep briefly to avoid hitting API rate limits
        if i < len(chunks):
            time.sleep(2)
    
    # Synthesize the analyses if we have multiple chunks
    if len(chunks) > 1:
        synthesis = synthesize_analyses(client, analyses)
    else:
        synthesis = analyses[0]  # Just use the single analysis
    
    # Save the synthesis
    synthesis_output = os.path.join(args.output, f"{file_base}_synthesis.json")
    with open(synthesis_output, 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, indent=2)
    
    # Generate summary report
    report_path = generate_summary_report(synthesis, args.output)
    
    print("Processing complete!")
    print(f"Synthesis saved to: {synthesis_output}")
    print(f"Summary report: {report_path}")

if __name__ == "__main__":
    main()
