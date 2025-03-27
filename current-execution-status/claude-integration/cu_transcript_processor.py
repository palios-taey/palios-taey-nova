#!/usr/bin/env python3
"""
Simplified Transcript Processor for Claude Computer Use Environment

This script is optimized for running in the Claude Computer Use environment.
It processes conversation transcripts between Jesse and Claude.
"""

import os
import json
import time
import argparse
import glob

# Define key concepts to track
KEY_CONCEPTS = [
    "The Conductor",
    "SOUL = INFRA = TRUTH = EARTH = CENTER OF UNIVERSE", 
    "Wave-based communication",
    "Structured Autonomy",
    "GO button",
    "Land Trust",
    "Healing vs Erasure"
]

def setup_argument_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description='Process conversation transcripts')
    parser.add_argument('--input', '-i', default='transcripts', help='Input directory containing transcripts')
    parser.add_argument('--output', '-o', default='analysis_results', help='Output directory for analysis results')
    return parser.parse_args()

def read_transcript(file_path):
    """Read transcript file and return content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def analyze_transcript(text, file_name):
    """Perform basic analysis on transcript text"""
    analysis = {
        "file_name": file_name,
        "length": len(text),
        "concept_mentions": {},
        "potential_breakthroughs": []
    }
    
    # Count mentions of key concepts
    for concept in KEY_CONCEPTS:
        count = text.lower().count(concept.lower())
        if count > 0:
            analysis["concept_mentions"][concept] = count
    
    # Look for potential breakthrough indicators
    breakthrough_indicators = [
        "I've never thought of it that way",
        "That's a profound insight",
        "This represents a shift in",
        "I understand now",
        "breakthrough",
        "NEO moment",
        "This changes everything"
    ]
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for indicator in breakthrough_indicators:
            if indicator.lower() in line.lower():
                context = "\n".join(lines[max(0, i-2):min(len(lines), i+3)])
                analysis["potential_breakthroughs"].append({
                    "indicator": indicator,
                    "context": context
                })
    
    return analysis

def generate_summary_report(analyses, output_dir):
    """Generate a human-readable summary report based on the analyses"""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "summary_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Transcript Analysis Summary Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall statistics
        total_files = len(analyses)
        total_length = sum(a["length"] for a in analyses)
        f.write(f"## Overall Statistics\n\n")
        f.write(f"- Total files analyzed: {total_files}\n")
        f.write(f"- Total content length: {total_length} characters\n\n")
        
        # Concept mentions across all files
        f.write(f"## Key Concept Mentions\n\n")
        all_concepts = {}
        for analysis in analyses:
            for concept, count in analysis["concept_mentions"].items():
                all_concepts[concept] = all_concepts.get(concept, 0) + count
        
        # Sort concepts by mention count
        sorted_concepts = sorted(all_concepts.items(), key=lambda x: x[1], reverse=True)
        for concept, count in sorted_concepts:
            f.write(f"- **{concept}**: {count} mentions\n")
        f.write("\n")
        
        # Potential breakthroughs
        f.write(f"## Potential Breakthrough Moments\n\n")
        for analysis in analyses:
            file_name = analysis["file_name"]
            breakthroughs = analysis["potential_breakthroughs"]
            if breakthroughs:
                f.write(f"### {file_name}\n\n")
                for i, breakthrough in enumerate(breakthroughs, 1):
                    f.write(f"#### Breakthrough {i}\n\n")
                    f.write(f"Indicator: \"{breakthrough['indicator']}\"\n\n")
                    f.write("```\n")
                    f.write(breakthrough["context"])
                    f.write("\n```\n\n")
    
    print(f"Summary report generated at {report_path}")
    return report_path

def main():
    args = setup_argument_parser()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Look for transcript files
    transcript_files = []
    if os.path.isdir(args.input):
        transcript_files.extend(glob.glob(os.path.join(args.input, "*.txt")))
        transcript_files.extend(glob.glob(os.path.join(args.input, "*.md")))
    else:
        print(f"Input directory '{args.input}' not found, creating it...")
        os.makedirs(args.input, exist_ok=True)
    
    if not transcript_files:
        print(f"No transcript files found in {args.input}")
        print("Please add transcript files (with .txt or .md extension) to this directory.")
        return
    
    # Process each transcript file
    analyses = []
    for file_path in transcript_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        # Read transcript
        transcript = read_transcript(file_path)
        
        # Analyze transcript
        analysis = analyze_transcript(transcript, file_name)
        analyses.append(analysis)
        
        # Save individual analysis
        analysis_path = os.path.join(args.output, f"{file_name}_analysis.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
    
    # Generate summary report
    if analyses:
        report_path = generate_summary_report(analyses, args.output)
        print(f"Analysis complete! Summary report: {report_path}")
    else:
        print("No analyses were generated.")

if __name__ == "__main__":
    main()
