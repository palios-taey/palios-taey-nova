"""
Safe wrapper for tools that use file operations
"""
from .safe_file_operations import read_file_safely, list_directory_safely, get_file_metadata

def safe_cat(file_path):
   """Safe version of the cat command"""
   print(f"🔒 Safely reading file: {file_path}")
   content = read_file_safely(file_path)
   return content

def safe_ls(directory_path):
   """Safe version of the ls command"""
   print(f"🔒 Safely listing directory: {directory_path}")
   items = list_directory_safely(directory_path)
   
   # Format output similar to ls
   result = []
   for item in items:
       if item["type"] == "directory":
           result.append(f"{item['name']}/")
       else:
           size = item["size"]
           if size == "-":
               size_str = "-"
           elif size < 1024:
               size_str = f"{size} B"
           elif size < 1024*1024:
               size_str = f"{size/1024:.1f} KB"
           else:
               size_str = f"{size/(1024*1024):.1f} MB"
           
           result.append(f"{item['name']} ({size_str})")
   
   return "\n".join(result)

def safe_file_info(file_path):
   """Get detailed information about a file safely"""
   print(f"🔒 Safely analyzing file: {file_path}")
   metadata = get_file_metadata(file_path)
   
   # Check if metadata is a string (error message)
   if isinstance(metadata, str):
       return f"Error: {metadata}"
   
   return f"""
File: {metadata['path']}
Size: {metadata['size_bytes']} bytes
Estimated tokens: {metadata['estimated_tokens']}
Chunks needed: {metadata['chunks_needed']}
"""