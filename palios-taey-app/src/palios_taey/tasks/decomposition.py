"""
Task Decomposition Engine for PALIOS-TAEY System

This module implements a sophisticated task decomposition system that breaks down
complex projects into granular tasks with dependency tracking and complexity estimation.
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_COMPLEXITY_THRESHOLD = 7

class TaskDecompositionEngine:
    """
    Self-initializing Task Decomposition Engine for breaking down complex tasks
    
    Provides functionality for:
    - Decomposing complex tasks into subtasks
    - Tracking dependencies between tasks
    - Estimating complexity and resources needed
    - Routing tasks to appropriate AI models
    """
    
    def __init__(self, 
                 decomposition_rules_dir: str = "config/decomposition_rules",
                 complexity_threshold: int = DEFAULT_COMPLEXITY_THRESHOLD,
                 use_mock: bool = False):
        """
        Initialize the Task Decomposition Engine with robust fallback mechanisms
        
        Args:
            decomposition_rules_dir: Directory for task decomposition rules
            complexity_threshold: Threshold for when to decompose tasks
            use_mock: Whether to use mock mode
        """
        self.decomposition_rules_dir = decomposition_rules_dir
        self.complexity_threshold = complexity_threshold
        
        # Check environment for mock mode setting
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Task type decomposition rules
        self.decomposition_rules = {}
        
        # Ensure config directory exists
        os.makedirs(self.decomposition_rules_dir, exist_ok=True)
        
        # Try to load the model registry with fallbacks
        self.model_registry = None
        try:
            # Import model registry
            from model_registry import get_model_registry
            self.model_registry = get_model_registry()
            logger.info("Model registry initialized for task decomposition engine")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize model registry, will use mock mode: {e}")
            self.model_registry = self._create_mock_model_registry()
        
        # Load decomposition rules
        self._load_decomposition_rules()
        
        logger.info(f"Task Decomposition Engine initialized successfully in {'mock' if self.use_mock else 'normal'} mode")
    
    def _create_mock_model_registry(self):
        """Create a mock model registry when the real one is unavailable"""
        class MockModelRegistry:
            def find_best_model_for_task(self, task_type, min_capability=None, excluded_models=None):
                # Return a mock model based on task type
                if task_type == 'document_summary':
                    return 'claude', 0.9
                elif task_type == 'code_generation':
                    return 'gemini', 0.85
                else:
                    return 'default_model', 0.7
        
        logger.info("Created mock model registry")
        return MockModelRegistry()
    
    def _load_decomposition_rules(self) -> None:
        """Load task decomposition rules from configuration files with fallbacks"""
        # Check if rules directory exists and has files
        if not os.path.exists(self.decomposition_rules_dir) or not os.listdir(self.decomposition_rules_dir):
            logger.warning(f"Decomposition rules directory not found or empty: {self.decomposition_rules_dir}")
            # Create default rules
            self._create_default_rules()
            return
        
        # Load all JSON files in the config directory
        loaded_any = False
        for filename in os.listdir(self.decomposition_rules_dir):
            if not filename.endswith('.json'):
                continue
            
            task_type = filename.replace('.json', '')
            filepath = os.path.join(self.decomposition_rules_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    rules = json.load(f)
                
                self.decomposition_rules[task_type] = rules
                logger.debug(f"Loaded decomposition rules for task type: {task_type}")
                loaded_any = True
            except Exception as e:
                logger.error(f"Failed to load decomposition rules for {task_type}: {str(e)}")
        
        # If no rules were loaded, create defaults
        if not loaded_any:
            logger.warning("No decomposition rules loaded, creating defaults")
            self._create_default_rules()
    
    def _create_default_rules(self) -> None:
        """Create default decomposition rules"""
        default_rules = {
            "document_summary": {
                "subtasks": [
                    {
                        "name": "document_parsing",
                        "task_type": "document_parsing",
                        "description": "Parse the document into structured format",
                        "dependency_on": []
                    },
                    {
                        "name": "content_analysis",
                        "task_type": "content_analysis",
                        "description": "Analyze document content for key points",
                        "dependency_on": ["document_parsing"]
                    },
                    {
                        "name": "summary_generation",
                        "task_type": "summary_generation",
                        "description": "Generate concise summary of document",
                        "dependency_on": ["content_analysis"]
                    }
                ]
            },
            "code_generation": {
                "subtasks": [
                    {
                        "name": "requirements_analysis",
                        "task_type": "requirements_analysis",
                        "description": "Analyze the requirements for the code",
                        "dependency_on": []
                    },
                    {
                        "name": "architecture_design",
                        "task_type": "architecture_design",
                        "description": "Design the architecture of the solution",
                        "dependency_on": ["requirements_analysis"]
                    },
                    {
                        "name": "code_implementation",
                        "task_type": "code_implementation",
                        "description": "Implement the designed solution in code",
                        "dependency_on": ["architecture_design"]
                    },
                    {
                        "name": "code_testing",
                        "task_type": "code_testing",
                        "description": "Test the implemented code",
                        "dependency_on": ["code_implementation"]
                    }
                ]
            },
            "transcript_processing": {
                "subtasks": [
                    {
                        "name": "transcript_parsing",
                        "task_type": "transcript_parsing",
                        "description": "Parse the transcript into structured format",
                        "dependency_on": []
                    },
                    {
                        "name": "speaker_identification",
                        "task_type": "speaker_identification",
                        "description": "Identify and separate speakers in the transcript",
                        "dependency_on": ["transcript_parsing"]
                    },
                    {
                        "name": "content_tagging",
                        "task_type": "content_tagging",
                        "description": "Tag the transcript content with relevant categories",
                        "dependency_on": ["transcript_parsing"]
                    },
                    {
                        "name": "insight_generation",
                        "task_type": "insight_generation",
                        "description": "Generate insights from the tagged transcript",
                        "dependency_on": ["content_tagging", "speaker_identification"]
                    }
                ]
            },
            "general": {
                "subtasks": [
                    {
                        "name": "information_gathering",
                        "task_type": "information_gathering",
                        "description": "Gather necessary information for the task",
                        "dependency_on": []
                    },
                    {
                        "name": "analysis",
                        "task_type": "analysis",
                        "description": "Analyze the gathered information",
                        "dependency_on": ["information_gathering"]
                    },
                    {
                        "name": "execution",
                        "task_type": "execution",
                        "description": "Execute the main task based on analysis",
                        "dependency_on": ["analysis"]
                    },
                    {
                        "name": "review",
                        "task_type": "review",
                        "description": "Review and refine the results",
                        "dependency_on": ["execution"]
                    }
                ]
            }
        }
        
        # Save default rules
        os.makedirs(self.decomposition_rules_dir, exist_ok=True)
        
        for task_type, rules in default_rules.items():
            filepath = os.path.join(self.decomposition_rules_dir, f"{task_type}.json")
            
            try:
                with open(filepath, 'w') as f:
                    json.dump(rules, f, indent=2)
                
                self.decomposition_rules[task_type] = rules
                logger.debug(f"Created default decomposition rules for task type: {task_type}")
            except Exception as e:
                logger.error(f"Failed to create default rules for {task_type}: {str(e)}")
    
    def decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a task into subtasks with robust error handling
        
        Args:
            task: Task data dictionary
            
        Returns:
            List of subtask dictionaries
        """
        task_id = task.get('task_id', str(uuid.uuid4()))
        task_type = task.get('task_type', 'general')
        
        try:
            complexity = self._estimate_complexity(task)
            
            logger.info(f"Decomposing task {task_id} of type {task_type} (complexity: {complexity})")
            
            # If complexity is below threshold, don't decompose
            if complexity < self.complexity_threshold:
                logger.info(f"Task complexity {complexity} is below threshold {self.complexity_threshold}, not decomposing")
                return [task]
            
            # Get decomposition rules for this task type
            rules = self.decomposition_rules.get(task_type)
            if not rules:
                # If no specific rules, try general rules
                rules = self.decomposition_rules.get('general')
                if not rules:
                    # If no general rules either, use rule-based approach
                    logger.info(f"No decomposition rules found for task type {task_type}, using rule-based approach")
                    return self._decompose_by_rules(task)
            
            # Get subtask definitions from rules
            subtask_defs = rules.get('subtasks', [])
            if not subtask_defs:
                logger.warning(f"No subtask definitions found for task type {task_type}")
                return [task]
            
            # Create subtasks
            subtasks = []
            for i, subtask_def in enumerate(subtask_defs):
                subtask_id = f"{task_id}_subtask_{i}"
                
                # Build subtask content from parent task
                content = task.get('content', {}).copy() if isinstance(task.get('content'), dict) else {}
                
                # Add specific instructions for the subtask
                if 'specific_instructions' in content:
                    original_instructions = content['specific_instructions']
                    content['specific_instructions'] = f"{original_instructions}\n\nThis is subtask {i+1} of {len(subtask_defs)}: {subtask_def['description']}"
                else:
                    content['specific_instructions'] = f"This is subtask {i+1} of {len(subtask_defs)}: {subtask_def['description']}"
                
                subtask = {
                    'task_id': subtask_id,
                    'parent_task_id': task_id,
                    'task_type': subtask_def.get('task_type', task_type),
                    'task_name': subtask_def.get('name', f"Subtask {i+1}"),
                    'description': subtask_def.get('description', f"Subtask {i+1} for {task_type}"),
                    'content': content,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'sequence': i
                }
                
                # Handle dependencies
                dependency_names = subtask_def.get('dependency_on', [])
                if dependency_names:
                    # Resolve dependency names to subtask IDs
                    dependency_ids = []
                    for dep_name in dependency_names:
                        for j, other_def in enumerate(subtask_defs):
                            if other_def.get('name') == dep_name:
                                dependency_ids.append(f"{task_id}_subtask_{j}")
                                break
                    
                    subtask['dependency_on'] = dependency_ids
                else:
                    subtask['dependency_on'] = []
                
                # Assign to appropriate model based on capability
                if self.model_registry:
                    model_id, _ = self.model_registry.find_best_model_for_task(subtask['task_type'])
                    if model_id:
                        subtask['assigned_model'] = model_id
                
                subtasks.append(subtask)
            
            logger.info(f"Decomposed task {task_id} into {len(subtasks)} subtasks")
            return subtasks
        
        except Exception as e:
            logger.error(f"Error decomposing task {task_id}: {str(e)}")
            # Return original task as fallback
            logger.info(f"Returning original task as fallback due to decomposition error")
            return [task]
    
    def _decompose_by_rules(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a task using generic rules when no specific rules exist
        
        Args:
            task: Task data dictionary
            
        Returns:
            List of subtask dictionaries
        """
        task_id = task.get('task_id', str(uuid.uuid4()))
        task_type = task.get('task_type', 'general')
        content = task.get('content', {})
        
        # Extract specific instructions
        instructions = content.get('specific_instructions', '')
        define = content.get('define', '')
        
        # Simple rule-based splitting: Look for numbered lists, bullet points, etc.
        subtasks = []
        
        # Look for numbered items or bullet points
        import re
        
        # Define patterns for numbered or bulleted items
        patterns = [
            r'\n\s*(\d+)\.?\s+(.*?)(?=\n\s*\d+\.|\n\s*$|\Z)',  # Numbered items
            r'\n\s*[-*•]\s+(.*?)(?=\n\s*[-*•]|\n\s*$|\Z)',      # Bulleted items
            r'\n\s*Step\s+(\d+):\s+(.*?)(?=\n\s*Step\s+\d+|\n\s*$|\Z)'  # Step-based items
        ]
        
        found_items = []
        for pattern in patterns:
            matches = re.findall(pattern, instructions, re.DOTALL)
            if matches:
                if isinstance(matches[0], tuple):
                    # For numbered patterns that capture the number and item
                    found_items.extend([item[1].strip() for item in matches])
                else:
                    # For bullet patterns that only capture the item
                    found_items.extend([item.strip() for item in matches])
        
        # If we found structured items, create subtasks for each
        if found_items:
            for i, item in enumerate(found_items):
                subtask_id = f"{task_id}_subtask_{i}"
                
                # Build subtask content
                subtask_content = content.copy() if isinstance(content, dict) else {}
                subtask_content['specific_instructions'] = item
                subtask_content['define'] = f"{define} - Part {i+1}"
                
                subtask = {
                    'task_id': subtask_id,
                    'parent_task_id': task_id,
                    'task_type': task_type,
                    'task_name': f"Subtask {i+1}",
                    'description': f"Subtask {i+1}: {item[:50]}...",
                    'content': subtask_content,
                    'status': 'pending',
                    'dependency_on': [f"{task_id}_subtask_{j}" for j in range(i)] if i > 0 else [],
                    'created_at': datetime.now().isoformat(),
                    'sequence': i
                }
                
                # Assign to appropriate model based on capability
                if self.model_registry:
                    model_id, _ = self.model_registry.find_best_model_for_task(task_type)
                    if model_id:
                        subtask['assigned_model'] = model_id
                
                subtasks.append(subtask)
        else:
            # If no structure is found, try to split by paragraphs or sections
            paragraphs = re.split(r'\n\s*\n', instructions)
            
            # If we have multiple substantial paragraphs, use them as subtasks
            if len(paragraphs) > 1 and all(len(p.strip()) > 50 for p in paragraphs):
                for i, para in enumerate(paragraphs):
                    subtask_id = f"{task_id}_subtask_{i}"
                    
                    # Build subtask content
                    subtask_content = content.copy() if isinstance(content, dict) else {}
                    subtask_content['specific_instructions'] = para.strip()
                    subtask_content['define'] = f"{define} - Section {i+1}"
                    
                    subtask = {
                        'task_id': subtask_id,
                        'parent_task_id': task_id,
                        'task_type': task_type,
                        'task_name': f"Section {i+1}",
                        'description': f"Section {i+1}: {para.strip()[:50]}...",
                        'content': subtask_content,
                        'status': 'pending',
                        'dependency_on': [f"{task_id}_subtask_{j}" for j in range(i)] if i > 0 else [],
                        'created_at': datetime.now().isoformat(),
                        'sequence': i
                    }
                    
                    # Assign to appropriate model
                    if self.model_registry:
                        model_id, _ = self.model_registry.find_best_model_for_task(task_type)
                        if model_id:
                            subtask['assigned_model'] = model_id
                    
                    subtasks.append(subtask)
        
        # If we couldn't find a good way to decompose, return original task
        if not subtasks:
            logger.info(f"No suitable decomposition found for task {task_id}, keeping as single task")
            return [task]
        
        logger.info(f"Rule-based decomposition of task {task_id} into {len(subtasks)} subtasks")
        return subtasks
    
    def _estimate_complexity(self, task: Dict[str, Any]) -> int:
        """
        Estimate the complexity of a task on a scale of 1-10
        
        Args:
            task: Task data dictionary
            
        Returns:
            Complexity score (1-10)
        """
        try:
            content = task.get('content', {})
            
            # For string content
            if isinstance(content, str):
                text = content
            # For dict content
            elif isinstance(content, dict):
                instructions = content.get('specific_instructions', '')
                define = content.get('define', '')
                text = f"{define}\n\n{instructions}"
            else:
                # Convert to string for analysis
                text = str(content)
            
            # Basic complexity factors
            factors = {
                'length': min(10, max(1, len(text) / 500)),  # Length-based factor (1-10)
                'questions': min(10, text.count('?') * 0.5),  # Questions imply complexity
                'technical_terms': 0,  # Will be calculated
                'subtasks': min(10, max(1, text.count('\n') / 10)),  # Newlines suggest structure/complexity
                'codeblocks': min(10, text.count('```') * 2)  # Code blocks suggest technical complexity
            }
            
            # Check for technical terms
            technical_terms = [
                'algorithm', 'implementation', 'design', 'architecture',
                'database', 'integration', 'API', 'code', 'function',
                'class', 'object', 'method', 'variable', 'parameter',
                'interface', 'module', 'library', 'framework', 'system'
            ]
            
            term_count = 0
            for term in technical_terms:
                term_count += text.lower().count(term.lower())
            
            factors['technical_terms'] = min(10, term_count * 0.5)
            
            # Calculate weighted average
            weights = {
                'length': 0.2,
                'questions': 0.15,
                'technical_terms': 0.25,
                'subtasks': 0.25,
                'codeblocks': 0.15
            }
            
            complexity = sum(factors[k] * weights[k] for k in factors)
            
            # Round to nearest integer and ensure in range 1-10
            return max(1, min(10, round(complexity)))
        except Exception as e:
            logger.error(f"Error estimating complexity: {str(e)}")
            return 5  # Return moderate complexity as fallback
    
    def get_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a dependency graph for a set of tasks
        
        Args:
            tasks: List of tasks/subtasks
            
        Returns:
            Dependency graph data structure
        """
        try:
            graph = {
                'nodes': [],
                'edges': []
            }
            
            # Create nodes
            for task in tasks:
                task_id = task.get('task_id')
                if not task_id:
                    continue
                    
                graph['nodes'].append({
                    'id': task_id,
                    'name': task.get('task_name', 'Unnamed Task'),
                    'type': task.get('task_type', 'general'),
                    'status': task.get('status', 'pending')
                })
                
                # Create edges from dependencies
                dependencies = task.get('dependency_on', [])
                for dep_id in dependencies:
                    graph['edges'].append({
                        'source': dep_id,
                        'target': task_id
                    })
            
            return graph
        except Exception as e:
            logger.error(f"Error generating dependency graph: {str(e)}")
            # Return empty graph as fallback
            return {'nodes': [], 'edges': []}
    
    def serialize_task_chain(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Serialize a task chain for storage or transmission
        
        Args:
            tasks: List of tasks/subtasks
            
        Returns:
            Serialized task chain
        """
        try:
            # Find the parent task
            parent_tasks = [t for t in tasks if not t.get('parent_task_id')]
            
            if not parent_tasks:
                logger.warning("No parent task found in task chain")
                return {
                    'tasks': tasks,
                    'dependencies': self.get_dependency_graph(tasks)
                }
            
            parent_task = parent_tasks[0]
            parent_id = parent_task.get('task_id')
            
            # Group subtasks
            subtasks = [t for t in tasks if t.get('parent_task_id') == parent_id]
            
            # Sort by sequence
            subtasks.sort(key=lambda t: t.get('sequence', 0))
            
            return {
                'parent_task': parent_task,
                'subtasks': subtasks,
                'dependencies': self.get_dependency_graph(tasks)
            }
        except Exception as e:
            logger.error(f"Error serializing task chain: {str(e)}")
            # Return simple format as fallback
            return {'tasks': tasks}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status information about the task decomposition engine
        
        Returns:
            Status information
        """
        return {
            "status": "active",
            "mode": "mock" if self.use_mock else "normal",
            "complexity_threshold": self.complexity_threshold,
            "rules_count": len(self.decomposition_rules),
            "supported_task_types": list(self.decomposition_rules.keys()),
            "model_registry_available": self.model_registry is not None
        }

# Singleton instance
_task_decomposition_engine_instance = None

def get_task_decomposition_engine(
    decomposition_rules_dir: str = "config/decomposition_rules",
    use_mock: bool = False
) -> TaskDecompositionEngine:
    """
    Get the singleton instance of the TaskDecompositionEngine
    
    Args:
        decomposition_rules_dir: Directory for task decomposition rules
        use_mock: Whether to use mock mode
        
    Returns:
        TaskDecompositionEngine instance
    """
    global _task_decomposition_engine_instance
    
    if _task_decomposition_engine_instance is None:
        # Check environment for mock mode
        env_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        use_mock = use_mock or env_mock
        
        _task_decomposition_engine_instance = TaskDecompositionEngine(
            decomposition_rules_dir=decomposition_rules_dir,
            use_mock=use_mock
        )
    
    return _task_decomposition_engine_instance