import os
import glob
import json
import tiktoken

# Directory containing cache files
cache_dir = "/home/computeruse/github/palios-taey-nova/claude-dc-implementation/cache"

# Initialize tokenizer - this approximates Claude's tokenization
encoding = tiktoken.get_encoding("cl100k_base")  # Claude-like tokenizer

def count_tokens_in_file(file_path):
    """Count tokens in a single file using local tokenizer"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Count tokens locally
        tokens = len(encoding.encode(content))
        bytes_size = os.path.getsize(file_path)
        
        return tokens, bytes_size, content
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0, ""

def main():
    # Get all files in the cache directory
    file_pattern = os.path.join(cache_dir, "*")
    files = glob.glob(file_pattern)
    
    # Sort files by name
    files.sort()
    
    # Store results
    results = []
    total_tokens = 0
    total_bytes = 0
    
    # Process each file
    for file_path in files:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            tokens, bytes_size, content = count_tokens_in_file(file_path)
            
            total_tokens += tokens
            total_bytes += bytes_size
            
            results.append({
                "filename": filename,
                "tokens": tokens,
                "bytes": bytes_size,
                "characters": len(content)
            })
            
            print(f"Processed: {filename}: {tokens} tokens, {bytes_size} bytes")
    
    # Print summary
    print("\nSummary:")
    print(f"Total files: {len(results)}")
    print(f"Total tokens: {total_tokens}")
    print(f"Total bytes: {total_bytes}")
    
    # Write detailed report to file
    report_path = os.path.join(cache_dir, "token_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            "total_tokens": total_tokens,
            "total_files": len(results),
            "total_bytes": total_bytes,
            "remaining_tokens": 200000 - total_tokens,  # Assuming 200K limit
            "files": results
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    print(f"Remaining tokens (assuming 200K limit): {200000 - total_tokens}")

if __name__ == "__main__":
    main()
