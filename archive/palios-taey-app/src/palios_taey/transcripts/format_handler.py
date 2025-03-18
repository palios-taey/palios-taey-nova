"""
Transcript Format Handler for PALIOS-TAEY System

This module handles the specific format for processed transcripts, including
parsing, validation, and conversion between different transcript formats.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_confidence_scores(summary_text: str) -> List[float]:
    """
    Parse confidence scores from summary format [score1,score2,score3]
    
    Args:
        summary_text: Summary text with confidence scores
        
    Returns:
        List of confidence scores
    """
    try:
        # Extract values between square brackets
        match = re.search(r'\[(.*?)\]', summary_text)
        if match:
            scores_text = match.group(1)
            scores = [float(score.strip()) for score in scores_text.split(',')]
            return scores
        return []
    except Exception as e:
        logger.warning(f"Error parsing confidence scores: {str(e)}")
        return []

def extract_summary_text(summary_text: str) -> str:
    """
    Extract clean summary text by removing confidence scores
    
    Args:
        summary_text: Summary text with confidence scores
        
    Returns:
        Clean summary text
    """
    try:
        # Remove everything between square brackets including the brackets
        clean_text = re.sub(r'\[.*?\]', '', summary_text).strip()
        return clean_text
    except Exception as e:
        logger.warning(f"Error extracting summary text: {str(e)}")
        return summary_text

def validate_transcript_format(sections: List[Dict[str, Any]]) -> bool:
    """
    Validate if sections follow the expected format
    
    Args:
        sections: List of transcript sections
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(sections, list):
        logger.error("Sections must be a list")
        return False
    
    for section in sections:
        # Check required fields
        if 'id' not in section:
            logger.error("Section missing 'id' field")
            return False
        
        if 'summary' not in section:
            logger.error(f"Section {section.get('id')} missing 'summary' field")
            return False
        
        if 'tags' not in section or not isinstance(section['tags'], list):
            logger.error(f"Section {section.get('id')} missing or invalid 'tags' field")
            return False
        
        # Validate tags structure
        for tag in section['tags']:
            if not all(key in tag for key in ['tag', 'topic', 'related']):
                logger.error(f"Section {section.get('id')} has tag with missing required fields")
                return False
    
    return True

def convert_to_standard_format(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert the DeepSearch format to the standard internal format
    
    Args:
        sections: List of transcript sections in DeepSearch format
        
    Returns:
        List of sections in standard format
    """
    standard_sections = []
    
    for section in sections:
        # Extract confidence scores and clean summary
        confidence_scores = parse_confidence_scores(section.get('summary', ''))
        clean_summary = extract_summary_text(section.get('summary', ''))
        
        # Create standardized tags
        standard_tags = []
        for tag in section.get('tags', []):
            standard_tag = {
                "category": tag.get('tag', '').replace('#', '').lower(),
                "value": tag.get('topic', ''),
                "related": tag.get('related', '')
            }
            standard_tags.append(standard_tag)
        
        # Create standard section
        standard_section = {
            "id": section.get('id', ''),
            "text": section.get('text', ''),  # May not be in DeepSearch format
            "summary": clean_summary,
            "confidence_scores": confidence_scores,
            "tags": standard_tags
        }
        
        standard_sections.append(standard_section)
    
    return standard_sections

def convert_to_deepsearch_format(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert internal format to the DeepSearch format
    
    Args:
        sections: List of transcript sections in standard format
        
    Returns:
        List of sections in DeepSearch format
    """
    deepsearch_sections = []
    
    for section in sections:
        # Format confidence scores
        confidence_str = ""
        if 'confidence_scores' in section and section['confidence_scores']:
            scores = section['confidence_scores']
            confidence_str = f"[{','.join([str(score) for score in scores])}] "
        
        # Create DeepSearch tags
        deepsearch_tags = []
        for tag in section.get('tags', []):
            deepsearch_tag = {
                "tag": f"#{tag.get('category', '').upper()}",
                "topic": tag.get('value', ''),
                "related": tag.get('related', '')
            }
            deepsearch_tags.append(deepsearch_tag)
        
        # Create DeepSearch section
        deepsearch_section = {
            "id": section.get('id', ''),
            "summary": f"{confidence_str}{section.get('summary', '')}",
            "tags": deepsearch_tags
        }
        
        deepsearch_sections.append(deepsearch_section)
    
    return deepsearch_sections

def parse_transcript_format(data: str) -> List[Dict[str, Any]]:
    """
    Parse transcript data from string (JSON)
    
    Args:
        data: JSON string with transcript sections
        
    Returns:
        List of parsed section dictionaries
    """
    try:
        sections = json.loads(data)
        if validate_transcript_format(sections):
            return convert_to_standard_format(sections)
        else:
            logger.error("Invalid transcript format")
            return []
    except Exception as e:
        logger.error(f"Error parsing transcript data: {str(e)}")
        return []

def format_transcript_for_export(sections: List[Dict[str, Any]]) -> str:
    """
    Format transcript sections for export (to DeepSearch format)
    
    Args:
        sections: List of transcript sections in standard format
        
    Returns:
        JSON string in DeepSearch format
    """
    try:
        deepsearch_sections = convert_to_deepsearch_format(sections)
        return json.dumps(deepsearch_sections, indent=2)
    except Exception as e:
        logger.error(f"Error formatting transcript for export: {str(e)}")
        return "[]"
