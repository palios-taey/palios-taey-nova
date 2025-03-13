"""
File deduplication strategy for PALIOS-TAEY codebase.

This script helps identify duplicate files in the codebase and
provides utilities for resolving duplications.
"""
import os
import difflib
import hashlib
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class FileInfo:
    """Information about a file."""
    
    path: str
    last_modified: datetime
    size: int
    hash: str
    
    @staticmethod
    def from_path(path: str) -> "FileInfo":
        """
        Create a FileInfo object from a file path.
        
        Args:
            path: Path to the file
            
        Returns:
            FileInfo object
        """
        stats = os.stat(path)
        last_modified = datetime.fromtimestamp(stats.st_mtime)
        size = stats.st_size
        
        # Calculate file hash
        hasher = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()
        
        return FileInfo(path=path, last_modified=last_modified, size=size, hash=file_hash)


@dataclass
class DuplicateGroup:
    """Group of duplicate files."""
    
    files: List[FileInfo]
    similarity: float  # 1.0 for exact duplicates, <1.0 for similar files
    
    def get_newest_file(self) -> FileInfo:
        """
        Get the most recently modified file in the group.
        
        Returns:
            Most recently modified FileInfo
        """
        return max(self.files, key=lambda f: f.last_modified)
    
    def get_original_file(self) -> Optional[FileInfo]:
        """
        Try to identify the 'original' file based on naming patterns.
        
        Returns:
            Original FileInfo or None if no original can be determined
        """
        # Prioritize files without version indicators in the name
        base_files = [
            f for f in self.files
            if not any(
                suffix in f.path
                for suffix in ["_v", "_new", "_old", "_backup", "_copy", "_temp"]
            )
        ]
        
        if base_files:
            # If we have base files, return the newest one
            return max(base_files, key=lambda f: f.last_modified)
        
        # Otherwise, just return the newest file
        return self.get_newest_file()


class DuplicationResolver:
    """Utility for finding and resolving duplicate files."""
    
    def __init__(self, root_dirs: List[str]):
        """
        Initialize the duplication resolver.
        
        Args:
            root_dirs: List of root directories to scan
        """
        self.root_dirs = root_dirs
        self.file_info_cache: Dict[str, FileInfo] = {}
    
    def scan_directories(self, extensions: Optional[List[str]] = None) -> Dict[str, FileInfo]:
        """
        Scan directories for files.
        
        Args:
            extensions: Optional list of file extensions to include
            
        Returns:
            Dictionary mapping file paths to FileInfo objects
        """
        if extensions is None:
            extensions = [".py", ".md", ".txt", ".json", ".yaml", ".yml"]
        
        for root_dir in self.root_dirs:
            for root, _, files in os.walk(root_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        path = os.path.join(root, file)
                        try:
                            self.file_info_cache[path] = FileInfo.from_path(path)
                        except (OSError, IOError):
                            print(f"Warning: Could not read file {path}")
        
        return self.file_info_cache
    
    def find_exact_duplicates(self) -> List[DuplicateGroup]:
        """
        Find exact duplicate files based on content hash.
        
        Returns:
            List of DuplicateGroup objects representing exact duplicates
        """
        # Group files by hash
        hash_groups: Dict[str, List[FileInfo]] = {}
        for file_info in self.file_info_cache.values():
            hash_groups.setdefault(file_info.hash, []).append(file_info)
        
        # Filter for groups with more than one file
        duplicate_groups = [
            DuplicateGroup(files=group, similarity=1.0)
            for group in hash_groups.values()
            if len(group) > 1
        ]
        
        return duplicate_groups
    
    def find_similar_files(self, threshold: float = 0.8) -> List[DuplicateGroup]:
        """
        Find similar (but not identical) files based on content comparison.
        
        Args:
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of DuplicateGroup objects representing similar files
        """
        # Group files by base name
        name_groups: Dict[str, List[FileInfo]] = {}
        for file_info in self.file_info_cache.values():
            base_name = os.path.splitext(os.path.basename(file_info.path))[0]
            # Strip version indicators
            base_name = base_name.split("_v")[0].split("_new")[0].split("_old")[0]
            name_groups.setdefault(base_name, []).append(file_info)
        
        # Filter for groups with more than one file
        candidate_groups = [
            group for group in name_groups.values() if len(group) > 1
        ]
        
        # Compare content for similarity
        duplicate_groups = []
        for group in candidate_groups:
            similar_groups = self._find_similar_in_group(group, threshold)
            duplicate_groups.extend(similar_groups)
        
        return duplicate_groups
    
    def _find_similar_in_group(
        self, group: List[FileInfo], threshold: float
    ) -> List[DuplicateGroup]:
        """
        Find similar files within a group.
        
        Args:
            group: Group of files to compare
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of DuplicateGroup objects
        """
        # Read file contents
        contents = {}
        for file_info in group:
            try:
                with open(file_info.path, "r", errors="ignore") as f:
                    contents[file_info.path] = f.read().splitlines()
            except (OSError, IOError):
                print(f"Warning: Could not read file {file_info.path}")
        
        # Compare each pair of files
        similar_groups = []
        grouped_files = set()
        
        for i, file1 in enumerate(group):
            if file1.path in grouped_files:
                continue
            
            similar_to_file1 = [file1]
            
            for file2 in group[i+1:]:
                if file2.path in grouped_files:
                    continue
                
                if file1.path in contents and file2.path in contents:
                    similarity = difflib.SequenceMatcher(
                        None, contents[file1.path], contents[file2.path]
                    ).ratio()
                    
                    if similarity >= threshold:
                        similar_to_file1.append(file2)
                        grouped_files.add(file2.path)
            
            if len(similar_to_file1) > 1:
                # Calculate average similarity
                avg_similarity = 0.0
                count = 0
                for i, f1 in enumerate(similar_to_file1):
                    for f2 in similar_to_file1[i+1:]:
                        if f1.path in contents and f2.path in contents:
                            similarity = difflib.SequenceMatcher(
                                None, contents[f1.path], contents[f2.path]
                            ).ratio()
                            avg_similarity += similarity
                            count += 1
                
                if count > 0:
                    avg_similarity /= count
                else:
                    avg_similarity = threshold
                
                similar_groups.append(
                    DuplicateGroup(files=similar_to_file1, similarity=avg_similarity)
                )
                grouped_files.add(file1.path)
        
        return similar_groups
   def generate_deduplication_report(self) -> Dict[str, any]:
       """
       Generate a comprehensive report on file duplications.
       
       Returns:
           Dictionary containing the deduplication report
       """
       exact_duplicates = self.find_exact_duplicates()
       similar_files = self.find_similar_files()
       
       report = {
           "exact_duplicates": [],
           "similar_files": [],
           "summary": {
               "total_files_scanned": len(self.file_info_cache),
               "exact_duplicate_groups": len(exact_duplicates),
               "similar_file_groups": len(similar_files),
               "total_duplicate_files": sum(len(group.files) - 1 for group in exact_duplicates),
               "total_similar_files": sum(len(group.files) - 1 for group in similar_files),
           },
           "recommendations": []
       }
       
       # Process exact duplicates
       for group in exact_duplicates:
           original = group.get_original_file()
           duplicates = [f for f in group.files if f != original]
           
           group_report = {
               "original": {
                   "path": original.path,
                   "last_modified": original.last_modified.isoformat(),
                   "size": original.size,
               },
               "duplicates": [
                   {
                       "path": f.path,
                       "last_modified": f.last_modified.isoformat(),
                       "size": f.size,
                   }
                   for f in duplicates
               ],
               "recommendation": f"Keep {original.path}, remove {len(duplicates)} duplicates"
           }
           report["exact_duplicates"].append(group_report)
           report["recommendations"].append(
               f"Replace duplicate files {', '.join(f.path for f in duplicates)} with {original.path}"
           )
       
       # Process similar files
       for group in similar_files:
           original = group.get_original_file()
           similar = [f for f in group.files if f != original]
           
           group_report = {
               "original": {
                   "path": original.path,
                   "last_modified": original.last_modified.isoformat(),
                   "size": original.size,
               },
               "similar_files": [
                   {
                       "path": f.path,
                       "last_modified": f.last_modified.isoformat(),
                       "size": f.size,
                   }
                   for f in similar
               ],
               "similarity": group.similarity,
               "recommendation": f"Review files to merge unique features into {original.path}"
           }
           report["similar_files"].append(group_report)
           report["recommendations"].append(
               f"Review and merge features from similar files {', '.join(f.path for f in similar)} into {original.path}"
           )
       
       return report
   
   def save_report(self, output_path: str) -> None:
       """
       Generate and save the deduplication report to a JSON file.
       
       Args:
           output_path: Path to save the report to
       """
       report = self.generate_deduplication_report()
       
       # Convert datetime objects to strings for JSON serialization
       report_json = json.dumps(report, indent=2, default=str)
       
       with open(output_path, "w") as f:
           f.write(report_json)
       
       print(f"Deduplication report saved to {output_path}")


# Example usage
if __name__ == "__main__":
   import sys
   
   if len(sys.argv) < 2:
       print("Usage: python file_deduplication.py <directory1> [<directory2> ...]")
       sys.exit(1)
   
   resolver = DuplicationResolver(sys.argv[1:])
   resolver.scan_directories()
   
   output_path = "deduplication_report.json"
   resolver.save_report(output_path)
