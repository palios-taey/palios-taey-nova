import json
import os

LOCAL_STORAGE = "./local_storage/"

def summarize_patterns(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    print("\n✨ Simple Human-Friendly Pattern Summary ✨\n")
    print(f"File: {os.path.basename(file_path)}")
    print(f"Pattern ID: {data.get('pattern_id', 'N/A')}")
    print(f"Harmony Index: {data.get('harmony_index', 'N/A'):.4f}\n")

    patterns = data.get('patterns', [])
    if not patterns:
        print("No patterns found.")
        return

    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. Category: {pattern.get('category', 'N/A')}")
        print(f"   Confidence: {pattern.get('confidence', 'N/A')}")
        print(f"   Keywords: {', '.join(pattern.get('keywords', []))}\n")

if __name__ == "__main__":
    files = sorted(os.listdir(LOCAL_STORAGE))
    
    if not files:
        print("No files found in local_storage.")
        exit()

    print("Pattern Files Found:")
    for idx, filename in enumerate(files, 1):
        print(f"{idx}: {filename}")

    choice = input("\nEnter the number of the file you want to view: ")
    try:
        file_idx = int(choice) - 1
        if file_idx < 0 or file_idx >= len(files):
            raise IndexError
        selected_file = os.path.join(LOCAL_STORAGE, files[file_idx])
        summarize_patterns(selected_file)
    except (ValueError, IndexError):
        print("Invalid choice. Please try again.")

