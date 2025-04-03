#!/usr/bin/env python3

import os
import sys
import anthropic
import json
from datetime import datetime

# Path to the cache directory
CACHE_DIR = "/home/jesse/projects/palios-taey-nova/claude-dc-implementation/cache"

# Initialize Anthropic client
client = anthropic.Anthropic()

def count_tokens_in_file(file_path):
    """Count tokens in a file using Anthropic's API"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Use Anthropic's token counting endpoint
        response = client.messages.count_tokens(
            model="claude-3-7-sonnet-20250219",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        
        # The response structure changed - extract the token count from the correct attribute
        token_count = response.usage.input_tokens  # Use this for newer API versions
        return token_count, os.path.getsize(file_path)
    except Exception as e:
        return f"Error: {str(e)}", os.path.getsize(file_path)

def format_size(size_in_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024 or unit == 'GB':
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024

def main():
    print(f"\nAnalyzing files in: {CACHE_DIR}\n")
    print(f"{'File Name':<40} {'Tokens':<10} {'Size':<10} {'Tokens/KB':<10}")
    print("-" * 70)
    
    total_tokens = 0
    total_size = 0
    results = []
    
    try:
        # Get all files in the directory
        files = [f for f in os.listdir(CACHE_DIR) if os.path.isfile(os.path.join(CACHE_DIR, f))]
        
        for file_name in files:
            file_path = os.path.join(CACHE_DIR, file_name)
            token_count, file_size = count_tokens_in_file(file_path)
            
            if isinstance(token_count, int):
                total_tokens += token_count
                total_size += file_size
                tokens_per_kb = token_count / (file_size / 1024) if file_size > 0 else 0
                
                result = {
                    "file_name": file_name,
                    "tokens": token_count,
                    "size_bytes": file_size,
                    "size_formatted": format_size(file_size),
                    "tokens_per_kb": round(tokens_per_kb, 2)
                }
                results.append(result)
                
                print(f"{file_name:<40} {token_count:<10} {format_size(file_size):<10} {round(tokens_per_kb, 2):<10}")
            else:
                print(f"{file_name:<40} {token_count:<50}")
        
        # Print summary
        if total_size > 0:
            avg_tokens_per_kb = total_tokens / (total_size / 1024)
            print("-" * 70)
            print(f"{'TOTAL':<40} {total_tokens:<10} {format_size(total_size):<10} {round(avg_tokens_per_kb, 2):<10}")
        
        # Save results to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"cache_token_analysis_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis_time": datetime.now().isoformat(),
                "cache_directory": CACHE_DIR,
                "total_tokens": total_tokens,
                "total_size_bytes": total_size,
                "total_size_formatted": format_size(total_size),
                "average_tokens_per_kb": round(avg_tokens_per_kb, 2) if total_size > 0 else 0,
                "files": results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}\n")
        
    except Exception as e:
        print(f"Error analyzing cache directory: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
