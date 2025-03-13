"""
Generate a repository report for CTO Claude.

This script analyzes the current repository structure and generates
a report with recommendations for next steps.
"""
import os
import json
import datetime
import argparse
from typing import Dict, List, Any


def scan_directory_structure(root_dir: str) -> Dict[str, Any]:
    """
    Scan the directory structure and return a nested representation.
    
    Args:
        root_dir: Root directory to scan
        
    Returns:
        Nested directory structure
    """
    result = {}
    
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        
        # Compute relative path
        rel_path = os.path.relpath(root, root_dir)
        if rel_path == ".":
            rel_path = ""
        
        # Initialize current directory in result
        current = result
        if rel_path:
            for part in rel_path.split(os.sep):
                current = current.setdefault(part, {})
        
        # Add files
        current["__files__"] = sorted([
            f for f in files
            if not f.startswith(".")
        ])
    
    return result


def generate_repository_report(repo_dir: str) -> Dict[str, Any]:
    """
    Generate a comprehensive repository report.
    
    Args:
        repo_dir: Repository directory
        
    Returns:
        Repository report
    """
    report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "repository_directory": os.path.abspath(repo_dir),
        "directory_structure": scan_directory_structure(repo_dir),
        "components": {
            "implemented": [],
            "missing": [],
        },
        "next_steps": [],
    }
    
    # Check for implemented components
    component_paths = [
        ("memory", "src/palios_taey/memory"),
        ("models", "src/palios_taey/models"),
        ("tasks", "src/palios_taey/tasks"),
        ("routing", "src/palios_taey/routing"),
        ("transcripts", "src/palios_taey/transcripts"),
        ("core", "src/palios_taey/core"),
        ("api", "src/palios_taey/api"),
    ]
    
    for name, path in component_paths:
        if os.path.exists(os.path.join(repo_dir, path)):
            report["components"]["implemented"].append({
                "name": name,
                "path": path,
                "files": os.listdir(os.path.join(repo_dir, path)),
            })
        else:
            report["components"]["missing"].append({
                "name": name,
                "path": path,
            })
    
    # Generate next steps recommendations
    if report["components"]["missing"]:
        report["next_steps"].append({
            "title": "Implement Missing Components",
            "description": "The following components need to be implemented: " + 
                           ", ".join(c["name"] for c in report["components"]["missing"]),
            "priority": "HIGH",
        })
    
    report["next_steps"].append({
        "title": "Set Up GitHub App for Claude Integration",
        "description": "Create a GitHub App with required permissions and configure the integration script",
        "priority": "HIGH",
    })
    
    report["next_steps"].append({
        "title": "Run File Deduplication Analysis",
        "description": "Use the deduplication script to analyze the archived repository and identify files to migrate",
        "priority": "MEDIUM",
    })
    
    report["next_steps"].append({
        "title": "Add Tests for All Components",
        "description": "Create comprehensive test suites for all implemented components",
        "priority": "MEDIUM",
    })
    
    report["next_steps"].append({
        "title": "Set Up CI/CD Pipeline",
        "description": "Create GitHub Actions workflows for continuous integration and deployment",
        "priority": "LOW",
    })
    
    return report


def save_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the repository report to a JSON file.
    
    Args:
        report: Repository report
        output_path: Path to save the report to
    """
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Repository report saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate a repository report")
    parser.add_argument("--repo-dir", default=".", help="Repository directory")
    parser.add_argument("--output", default="repository_report.json", help="Output file path")
    
    args = parser.parse_args()
    
    report = generate_repository_report(args.repo_dir)
    save_report(report, args.output)


if __name__ == "__main__":
    main()
