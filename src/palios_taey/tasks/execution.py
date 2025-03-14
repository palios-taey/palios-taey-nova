"""
Task Execution Engine for PALIOS-TAEY System

This module implements the core task execution and orchestration system,
managing the task lifecycle and coordinating with AI models.
"""

import os
import json
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default task execution settings
DEFAULT_MAX_WORKERS = 5
DEFAULT_MAX_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5

class TaskExecutionEngine:
    """
    Self-initializing Task Execution Engine for orchestrating task execution
    
    Provides functionality for:
    - Managing task lifecycle from creation to completion
    - Executing tasks using appropriate AI models
    - Tracking task status and handling dependencies
    - Aggregating results from subtasks
    """
    
    def __init__(self, 
                 max_workers: int = DEFAULT_MAX_WORKERS,
                 max_retry_count: int = DEFAULT_MAX_RETRY_COUNT,
                 retry_delay: int = DEFAULT_RETRY_DELAY,
                 store_func: Optional[Callable] = None,
                 retrieve_func: Optional[Callable] = None,
                 use_mock: bool = False):
        """
        Initialize the Task Execution Engine with robust fallback mechanisms
        
        Args:
            max_workers: Maximum number of concurrent task executions
            max_retry_count: Maximum number of retry attempts for failed tasks
            retry_delay: Delay in seconds between retry attempts
            store_func: Function for storing task data
            retrieve_func: Function for retrieving task data
            use_mock: Whether to use mock mode
        """
        self.max_workers = max_workers
        self.max_retry_count = max_retry_count
        self.retry_delay = retry_delay
        
        # Check environment for mock mode setting
        self.use_mock = use_mock or os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        
        # Initialize storage functions
        self.store_func = store_func
        self.retrieve_func = retrieve_func
        
        # If no storage functions provided, create in-memory storage
        if not store_func or not retrieve_func or self.use_mock:
            logger.info("Using in-memory storage for task execution engine")
            self._memory_storage = {}
            
            # Create memory-based storage functions
            if not store_func or self.use_mock:
                self.store_func = self._memory_store
            
            if not retrieve_func or self.use_mock:
                self.retrieve_func = self._memory_retrieve
        
        # Active tasks being executed
        self.active_tasks = {}
        
        # Task results
        self.task_results = {}
        
        # Task executor pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Try to import required components with fallbacks
        self.model_registry = None
        self.decomposer = None
        
        try:
            # Import model registry
            from model_registry import get_model_registry
            self.model_registry = get_model_registry()
            logger.info("Model registry initialized for task execution engine")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize model registry, will use mock mode: {e}")
            self.model_registry = self._create_mock_model_registry()
        
        try:
            # Import task decomposition engine
            from task_decomposition import get_task_decomposition_engine
            self.decomposer = get_task_decomposition_engine()
            logger.info("Task decomposition engine initialized for task execution engine")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize task decomposition engine, will use mock mode: {e}")
            self.decomposer = self._create_mock_decomposer()
        
        # Import AI services with mock fallback
        try:
            import ai_services
            self.ai_services = ai_services
        except ImportError:
            logger.warning("AI services module not found, using mock implementation")
            # Create mock AI services
            from types import ModuleType
            self.ai_services = ModuleType('ai_services')
            self.ai_services.execute_task = self._mock_execute_task
        
        logger.info(f"Task Execution Engine initialized successfully in {'mock' if self.use_mock else 'normal'} mode")
    
    def _memory_store(self, task: Dict[str, Any]) -> str:
        """In-memory task storage function"""
        task_id = task.get('task_id', str(uuid.uuid4()))
        self._memory_storage[task_id] = task.copy()
        return task_id
    
    def _memory_retrieve(self, task_id: str) -> Optional[Dict[str, Any]]:
        """In-memory task retrieval function"""
        return self._memory_storage.get(task_id)
    
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
            
            def record_performance(self, model_id, task_type, performance_metrics, learn=True):
                # Just log the performance
                logger.debug(f"Mock performance recorded for {model_id} on {task_type}: {performance_metrics}")
                return True
            
            def get_model_capabilities(self, model_id):
                # Return mock capabilities
                return {'general': 0.8, 'document_summary': 0.7, 'code_generation': 0.7}
        
        logger.info("Created mock model registry")
        return MockModelRegistry()
    
    def _create_mock_decomposer(self):
        """Create a mock task decomposer when the real one is unavailable"""
        class MockTaskDecomposer:
            def __init__(self):
                self.complexity_threshold = 7
            
            def _estimate_complexity(self, task):
                # Simple complexity estimation based on content length
                content = task.get('content', {})
                text = json.dumps(content)
                return min(10, max(1, len(text) / 500))
            
            def decompose_task(self, task):
                # Simple task decomposition into sequential subtasks
                task_id = task.get('task_id', 'unknown')
                task_type = task.get('task_type', 'general')
                
                complexity = self._estimate_complexity(task)
                if complexity < self.complexity_threshold:
                    return [task]
                
                # Create 2-3 subtasks based on complexity
                num_subtasks = 2 if complexity < 8 else 3
                subtasks = []
                
                for i in range(num_subtasks):
                    subtask_id = f"{task_id}_subtask_{i}"
                    subtask = {
                        'task_id': subtask_id,
                        'parent_task_id': task_id,
                        'task_type': task_type,
                        'task_name': f"Subtask {i+1}",
                        'description': f"Subtask {i+1} for {task_type}",
                        'content': task.get('content', {}).copy(),
                        'status': 'pending',
                        'dependency_on': [f"{task_id}_subtask_{j}" for j in range(i)] if i > 0 else [],
                        'created_at': datetime.now().isoformat(),
                        'sequence': i
                    }
                    subtasks.append(subtask)
                
                return subtasks
            
            def get_dependency_graph(self, tasks):
                # Create a simple dependency graph
                graph = {
                    'nodes': [],
                    'edges': []
                }
                
                for task in tasks:
                    task_id = task.get('task_id')
                    graph['nodes'].append({
                        'id': task_id,
                        'name': task.get('task_name', 'Unnamed Task'),
                        'type': task.get('task_type', 'general'),
                        'status': task.get('status', 'pending')
                    })
                    
                    dependencies = task.get('dependency_on', [])
                    for dep_id in dependencies:
                        graph['edges'].append({
                            'source': dep_id,
                            'target': task_id
                        })
                
                return graph
        
        logger.info("Created mock task decomposer")
        return MockTaskDecomposer()
    
    def _mock_execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation of AI task execution"""
        # Extract task type for response customization
        task_type = task_data.get('task_type', 'general')
        
        # Add delay to simulate processing
        time.sleep(0.5)
        
        # Generate appropriate mock response based on task type
        if task_type == 'document_summary':
            return {
                "result": "This is a mock summary of the document. It covers the main points and provides a concise overview.",
                "model": "mock_model",
                "status": "completed"
            }
        
        elif task_type == 'code_generation':
            return {
                "result": """```python
def example_function():
    \"\"\"This is a mock function for testing purposes\"\"\"
    print("Hello from mock code generation!")
    return {"status": "success"}
```

This code demonstrates a simple Python function that returns a status object.""",
                "model": "mock_model",
                "status": "completed"
            }
        
        elif task_type == 'transcript_processing':
            return {
                "result": json.dumps([
                    {"id": "1", "summary": "Introduction to the meeting", "tags": [{"tag": "#TOPIC", "topic": "Introduction", "related": ""}]},
                    {"id": "2", "summary": "Discussion of project timeline", "tags": [{"tag": "#TOPIC", "topic": "Timeline", "related": "Project"}]}
                ]),
                "model": "mock_model",
                "status": "completed"
            }
        
        else:
            return {
                "result": f"This is a mock response for task type: {task_type}. In a real environment, this would be generated by an AI model.",
                "model": "mock_model",
                "status": "completed"
            }
    
    def submit_task(self, task: Dict[str, Any], auto_execute: bool = True) -> str:
        """
        Submit a new task for execution
        
        Args:
            task: Task data dictionary
            auto_execute: Whether to automatically start execution
            
        Returns:
            Task ID
        """
        # Ensure task has an ID
        if 'task_id' not in task:
            task['task_id'] = str(uuid.uuid4())
        
        task_id = task['task_id']
        
        # Add missing fields
        if 'status' not in task:
            task['status'] = 'pending'
        
        if 'created_at' not in task:
            task['created_at'] = datetime.now().isoformat()
        
        if 'assigned_model' not in task:
            # Auto-assign model based on task type
            if self.model_registry:
                model_id, score = self.model_registry.find_best_model_for_task(task.get('task_type', 'general'))
                if model_id:
                    task['assigned_model'] = model_id
                    logger.debug(f"Auto-assigned model {model_id} (score {score}) to task {task_id}")
            else:
                # If model registry is not available, use a default model
                task['assigned_model'] = 'default_model'
                logger.warning(f"Model registry not available, using default model for task {task_id}")
        
        # Store task
        if self.store_func:
            try:
                self.store_func(task)
            except Exception as e:
                logger.error(f"Failed to store task {task_id}: {str(e)}")
                # Continue processing even if storage fails
        
        logger.info(f"Task {task_id} submitted successfully")
        
        # Start execution if requested
        if auto_execute:
            try:
                self.execute_task(task_id, task)
            except Exception as e:
                logger.error(f"Failed to execute task {task_id}: {str(e)}")
                # Update task with error status
                task['status'] = 'failed'
                task['error'] = str(e)
                task['completed_at'] = datetime.now().isoformat()
                
                # Store updated task
                if self.store_func:
                    try:
                        self.store_func(task)
                    except Exception as store_error:
                        logger.error(f"Failed to update failed task {task_id}: {str(store_error)}")
        
        return task_id
    
    def execute_task(self, 
                    task_id: str, 
                    task: Optional[Dict[str, Any]] = None,
                    force_decompose: bool = False) -> Future:
        """
        Execute a task
        
        Args:
            task_id: Task identifier
            task: Task data dictionary (retrieved if not provided)
            force_decompose: Force decomposition even if complexity is low
            
        Returns:
            Future representing the task execution
        """
        # Get task if not provided
        if task is None:
            task = self._get_task(task_id)
            if task is None:
                error_msg = f"Task {task_id} not found"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Check if task is already being executed
        if task_id in self.active_tasks:
            logger.warning(f"Task {task_id} is already being executed")
            return self.active_tasks[task_id]
        
        # Update task status
        task['status'] = 'processing'
        task['started_at'] = datetime.now().isoformat()
        
        # Store updated task
        if self.store_func:
            try:
                self.store_func(task)
            except Exception as e:
                logger.error(f"Failed to update task {task_id}: {str(e)}")
        
        # Submit task for execution
        future = self.executor.submit(self._execute_task_internal, task_id, task, force_decompose)
        self.active_tasks[task_id] = future
        
        logger.info(f"Task {task_id} execution started")
        return future
    
    def _execute_task_internal(self, 
                              task_id: str, 
                              task: Dict[str, Any],
                              force_decompose: bool) -> Dict[str, Any]:
        """
        Internal method for task execution
        
        Args:
            task_id: Task identifier
            task: Task data dictionary
            force_decompose: Force decomposition even if complexity is low
            
        Returns:
            Task result
        """
        try:
            # Check if task should be decomposed
            if not self.decomposer:
                # No decomposer available, execute directly
                logger.info(f"No decomposer available, executing task {task_id} directly")
                return self._execute_simple_task(task_id, task)
            
            complexity = self.decomposer._estimate_complexity(task)
            
            if complexity >= self.decomposer.complexity_threshold or force_decompose:
                logger.info(f"Task {task_id} complexity {complexity} exceeds threshold, decomposing")
                return self._execute_complex_task(task_id, task)
            else:
                logger.info(f"Executing task {task_id} directly (complexity {complexity})")
                return self._execute_simple_task(task_id, task)
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}", exc_info=True)
            
            # Update task status
            task['status'] = 'failed'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()
            
            # Store updated task
            if self.store_func:
                try:
                    self.store_func(task)
                except Exception as store_error:
                    logger.error(f"Failed to update failed task {task_id}: {str(store_error)}")
            
            # Return error result
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def _execute_simple_task(self, task_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a simple task directly using the assigned model
        
        Args:
            task_id: Task identifier
            task: Task data dictionary
            
        Returns:
            Task result
        """
        model_id = task.get('assigned_model')
        if not model_id:
            # Try to find best model
            if self.model_registry:
                model_id, _ = self.model_registry.find_best_model_for_task(task.get('task_type', 'general'))
            
            if not model_id:
                # Use default model as fallback
                model_id = 'default_model'
                logger.warning(f"No suitable model found for task {task_id}, using default model")
            
            task['assigned_model'] = model_id
        
        # Execute with retry logic
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retry_count:
            try:
                logger.info(f"Executing task {task_id} with model {model_id} (attempt {retry_count + 1})")
                
                # Execute task using AI service
                result = self.ai_services.execute_task(task)
                
                # Record performance if model registry is available
                if self.model_registry:
                    self.model_registry.record_performance(
                        model_id=model_id,
                        task_type=task.get('task_type', 'general'),
                        performance_metrics={
                            'success': True,
                            'execution_time': (datetime.now() - datetime.fromisoformat(task['started_at'])).total_seconds(),
                            'retry_count': retry_count
                        }
                    )
                
                # Update task
                task['status'] = 'completed'
                task['result'] = result
                task['completed_at'] = datetime.now().isoformat()
                
                # Store task result
                self.task_results[task_id] = result
                
                # Store updated task
                if self.store_func:
                    try:
                        self.store_func(task)
                    except Exception as e:
                        logger.error(f"Failed to store task result for {task_id}: {str(e)}")
                
                logger.info(f"Task {task_id} completed successfully")
                return result
            
            except Exception as e:
                last_error = e
                logger.warning(f"Task {task_id} execution failed (attempt {retry_count + 1}): {str(e)}")
                
                retry_count += 1
                
                if retry_count <= self.max_retry_count:
                    # Wait before retry
                    time.sleep(self.retry_delay)
                    
                    # Try with a different model if available
                    if retry_count == self.max_retry_count // 2 and self.model_registry:
                        # Get alternative model
                        excluded_models = [model_id]
                        alt_model, _ = self.model_registry.find_best_model_for_task(
                            task.get('task_type', 'general'),
                            excluded_models=excluded_models
                        )
                        
                        if alt_model:
                            logger.info(f"Switching to alternative model {alt_model} for task {task_id}")
                            model_id = alt_model
                            task['assigned_model'] = model_id
        
        # All retries failed
        # Record performance if model registry is available
        if self.model_registry:
            self.model_registry.record_performance(
                model_id=model_id,
                task_type=task.get('task_type', 'general'),
                performance_metrics={
                    'success': False,
                    'execution_time': (datetime.now() - datetime.fromisoformat(task['started_at'])).total_seconds(),
                    'retry_count': retry_count,
                    'error': str(last_error)
                }
            )
        
        # Update task
        task['status'] = 'failed'
        task['error'] = str(last_error)
        task['completed_at'] = datetime.now().isoformat()
        
        # Store updated task
        if self.store_func:
            try:
                self.store_func(task)
            except Exception as e:
                logger.error(f"Failed to store failed task {task_id}: {str(e)}")
        
        logger.error(f"Task {task_id} failed after {retry_count} attempts")
        
        # Return an error result instead of raising to allow better handling
        error_result = {
            'task_id': task_id,
            'status': 'failed',
            'error': str(last_error),
            'model': model_id
        }
        
        self.task_results[task_id] = error_result
        return error_result
    
    def _execute_complex_task(self, task_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complex task by decomposing it into subtasks
        
        Args:
            task_id: Task identifier
            task: Task data dictionary
            
        Returns:
            Aggregated result from subtasks
        """
        # Decompose task
        try:
            subtasks = self.decomposer.decompose_task(task)
        except Exception as e:
            logger.error(f"Error decomposing task {task_id}: {str(e)}")
            # Fall back to simple execution
            logger.info(f"Falling back to simple execution for task {task_id}")
            return self._execute_simple_task(task_id, task)
        
        # If only one task is returned, it wasn't decomposed
        if len(subtasks) == 1:
            logger.info(f"Task {task_id} wasn't decomposed, executing directly")
            return self._execute_simple_task(task_id, task)
        
        # Update parent task
        task['has_subtasks'] = True
        task['subtask_count'] = len(subtasks)
        task['subtasks_completed'] = 0
        
        # Store updated task
        if self.store_func:
            try:
                self.store_func(task)
            except Exception as e:
                logger.error(f"Failed to update parent task {task_id}: {str(e)}")
        
        # Execute subtasks
        logger.info(f"Executing {len(subtasks)} subtasks for task {task_id}")
        
        # Submit all subtasks
        for subtask in subtasks:
            subtask_id = subtask['task_id']
            self.submit_task(subtask, auto_execute=False)
        
        # Build dependency graph
        try:
            dependency_graph = self.decomposer.get_dependency_graph(subtasks)
        except Exception as e:
            logger.error(f"Error building dependency graph for task {task_id}: {str(e)}")
            # Create simple dependency graph based on sequence
            dependency_graph = {
                'nodes': [{'id': st['task_id']} for st in subtasks],
                'edges': []
            }
            for i, st in enumerate(subtasks):
                if i > 0:
                    dependency_graph['edges'].append({
                        'source': subtasks[i-1]['task_id'],
                        'target': st['task_id']
                    })
        
        # Find tasks with no dependencies
        ready_tasks = []
        for st in subtasks:
            if not st.get('dependency_on'):
                ready_tasks.append(st)
        
        # If no ready tasks found, use first subtask as fallback
        if not ready_tasks and subtasks:
            ready_tasks = [subtasks[0]]
        
        # Execute tasks in dependency order
        results = {}
        while ready_tasks:
            # Execute ready tasks
            futures = []
            for subtask in ready_tasks:
                subtask_id = subtask['task_id']
                futures.append((subtask_id, self.execute_task(subtask_id, subtask)))
            
            # Wait for all to complete
            for subtask_id, future in futures:
                try:
                    result = future.result()
                    results[subtask_id] = result
                    
                    # Update parent task
                    task['subtasks_completed'] = task.get('subtasks_completed', 0) + 1
                    
                    # Store updated task
                    if self.store_func:
                        try:
                            self.store_func(task)
                        except Exception as e:
                            logger.error(f"Failed to update parent task {task_id}: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Subtask {subtask_id} failed: {str(e)}")
                    results[subtask_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    
                    # Handle subtask failure
                    if any(st.get('critical', False) for st in subtasks if st['task_id'] == subtask_id):
                        # Critical subtask failure causes parent task to fail
                        task['status'] = 'failed'
                        task['error'] = f"Critical subtask {subtask_id} failed: {str(e)}"
                        task['completed_at'] = datetime.now().isoformat()
                        
                        # Store updated task
                        if self.store_func:
                            try:
                                self.store_func(task)
                            except Exception as store_error:
                                logger.error(f"Failed to update failed task {task_id}: {str(store_error)}")
                        
                        # Return failure
                        return {
                            'task_id': task_id,
                            'status': 'failed',
                            'error': f"Critical subtask {subtask_id} failed: {str(e)}",
                            'completed_at': datetime.now().isoformat()
                        }
            
            # Find next batch of ready tasks
            completed_ids = set(results.keys())
            ready_tasks = []
            
            for subtask in subtasks:
                subtask_id = subtask['task_id']
                
                # Skip already completed tasks
                if subtask_id in completed_ids:
                    continue
                
                # Check if all dependencies are satisfied
                dependencies = subtask.get('dependency_on', [])
                if all(dep_id in completed_ids for dep_id in dependencies):
                    ready_tasks.append(subtask)
        
        # All subtasks completed
        # Aggregate results
        aggregated_result = self._aggregate_results(task, subtasks, results)
        
        # Update task
        task['status'] = 'completed'
        task['result'] = aggregated_result
        task['completed_at'] = datetime.now().isoformat()
        
        # Store task result
        self.task_results[task_id] = aggregated_result
        
        # Store updated task
        if self.store_func:
            try:
                self.store_func(task)
            except Exception as e:
                logger.error(f"Failed to store task result for {task_id}: {str(e)}")
        
        logger.info(f"Complex task {task_id} completed successfully")
        return aggregated_result
    
    def _aggregate_results(self, 
                          parent_task: Dict[str, Any], 
                          subtasks: List[Dict[str, Any]], 
                          results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate results from subtasks
        
        Args:
            parent_task: Parent task dictionary
            subtasks: List of subtask dictionaries
            results: Dictionary mapping subtask IDs to results
            
        Returns:
            Aggregated result
        """
        task_type = parent_task.get('task_type', 'general')
        
        # Get ordered subtasks
        ordered_subtasks = sorted(subtasks, key=lambda t: t.get('sequence', 0))
        
        # Basic aggregation - combine results in order
        aggregate = {
            "task_id": parent_task['task_id'],
            "status": "completed",
            "subtask_results": {},
            "aggregated_data": {}
        }
        
        # Add subtask results
        for subtask in ordered_subtasks:
            subtask_id = subtask['task_id']
            if subtask_id in results:
                aggregate['subtask_results'][subtask_id] = results[subtask_id]
        
        # Check for failed subtasks
        failed_subtasks = [sid for sid, res in results.items() 
                         if isinstance(res, dict) and res.get('status') == 'failed']
        
        if failed_subtasks:
            # Some subtasks failed, but we'll continue with aggregation
            aggregate["has_failures"] = True
            aggregate["failed_subtasks"] = failed_subtasks
        
        # Task type specific aggregation
        if task_type == 'document_summary':
            # Combine summaries
            summary_parts = []
            for subtask in ordered_subtasks:
                subtask_id = subtask['task_id']
                if subtask_id in results:
                    result = results[subtask_id]
                    if isinstance(result, dict) and 'result' in result:
                        summary_parts.append(result['result'])
                    else:
                        summary_parts.append(str(result))
            
            aggregate['aggregated_data']['combined_summary'] = "\n\n".join(summary_parts)
        
        elif task_type == 'code_generation':
            # Combine code
            code_parts = []
            for subtask in ordered_subtasks:
                subtask_id = subtask['task_id']
                if subtask_id in results:
                    result = results[subtask_id]
                    if isinstance(result, dict) and 'result' in result:
                        code_parts.append(result['result'])
                    else:
                        code_parts.append(str(result))
            
            aggregate['aggregated_data']['combined_code'] = "\n\n".join(code_parts)
        
        elif task_type == 'transcript_processing':
            # Combine transcript analysis
            analysis_parts = []
            tags = []
            
            for subtask in ordered_subtasks:
                subtask_id = subtask['task_id']
                if subtask_id in results:
                    result = results[subtask_id]
                    if isinstance(result, dict):
                        if 'result' in result:
                            analysis_parts.append(result['result'])
                        if 'tags' in result:
                            tags.extend(result['tags'])
                    else:
                        analysis_parts.append(str(result))
            
            aggregate['aggregated_data']['combined_analysis'] = "\n\n".join(analysis_parts)
            aggregate['aggregated_data']['tags'] = tags
        
        else:
            # Default aggregation
            all_results = []
            for subtask in ordered_subtasks:
                subtask_id = subtask['task_id']
                if subtask_id in results:
                    result = results[subtask_id]
                    if isinstance(result, dict) and 'result' in result:
                        all_results.append(result['result'])
                    else:
                        all_results.append(str(result))
            
            aggregate['aggregated_data']['combined_result'] = "\n\n".join(all_results)
        
        return aggregate
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary
        """
        # Try to get from storage
        task = self._get_task(task_id)
        
        if task is None:
            logger.warning(f"Task {task_id} not found")
            return {
                'task_id': task_id,
                'status': 'not_found'
            }
        
        # Check if task is active
        is_active = task_id in self.active_tasks
        
        status = {
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'created_at': task.get('created_at'),
            'started_at': task.get('started_at'),
            'completed_at': task.get('completed_at'),
            'has_subtasks': task.get('has_subtasks', False),
            'subtask_count': task.get('subtask_count', 0),
            'subtasks_completed': task.get('subtasks_completed', 0),
            'is_active': is_active
        }
        
        # Include error if present
        if 'error' in task:
            status['error'] = task['error']
        
        # Include result if task is completed
        if task.get('status') == 'completed' and 'result' in task:
            status['result'] = task['result']
        
        return status
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Whether cancellation was successful
        """
        # Check if task is active
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} is not active, cannot cancel")
            return False
        
        # Cancel the future
        future = self.active_tasks[task_id]
        cancelled = future.cancel()
        
        if cancelled:
            logger.info(f"Task {task_id} cancelled successfully")
            
            # Remove from active tasks
            del self.active_tasks[task_id]
            
            # Update task status
            task = self._get_task(task_id)
            if task:
                task['status'] = 'cancelled'
                task['cancelled_at'] = datetime.now().isoformat()
                
                # Store updated task
                if self.store_func:
                    try:
                        self.store_func(task)
                    except Exception as e:
                        logger.error(f"Failed to update cancelled task {task_id}: {str(e)}")
            
            return True
        else:
            logger.warning(f"Failed to cancel task {task_id}")
            return False
    
    def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task dictionary or None if not found
        """
        if self.retrieve_func:
            try:
                return self.retrieve_func(task_id)
            except Exception as e:
                logger.error(f"Failed to retrieve task {task_id}: {str(e)}")
        
        return None
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get a list of active tasks
        
        Returns:
            List of active task dictionaries
        """
        active_task_info = []
        
        for task_id in self.active_tasks.keys():
            task = self._get_task(task_id)
            if task:
                active_task_info.append({
                    'task_id': task_id,
                    'task_type': task.get('task_type', 'unknown'),
                    'status': task.get('status', 'unknown'),
                    'started_at': task.get('started_at'),
                    'has_subtasks': task.get('has_subtasks', False)
                })
        
        return active_task_info
    
    def get_all_tasks(self, limit: int = 100, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of all tasks (limited to in-memory storage implementation)
        
        Args:
            limit: Maximum number of tasks to return
            task_type: Optional task type to filter by
            
        Returns:
            List of task dictionaries
        """
        # This only works with in-memory storage
        if not hasattr(self, '_memory_storage'):
            logger.warning("get_all_tasks() only supported with in-memory storage")
            return []
        
        # Get all tasks from storage
        tasks = list(self._memory_storage.values())
        
        # Filter by task type if specified
        if task_type:
            tasks = [t for t in tasks if t.get('task_type') == task_type]
        
        # Sort by created_at timestamp (most recent first)
        tasks.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        
        # Limit results
        return tasks[:limit]
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the task execution engine
        
        Args:
            wait: Whether to wait for active tasks to complete
        """
        self.executor.shutdown(wait=wait)
        logger.info(f"Task Execution Engine shutdown {'completed' if wait else 'initiated'}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the task execution engine
        
        Returns:
            Status information
        """
        return {
            "status": "active",
            "mode": "mock" if self.use_mock else "normal",
            "active_tasks": len(self.active_tasks),
            "max_workers": self.max_workers,
            "model_registry_available": self.model_registry is not None,
            "decomposer_available": self.decomposer is not None
        }

# Singleton instance
_task_execution_engine_instance = None

def get_task_execution_engine(
    store_func: Optional[Callable] = None,
    retrieve_func: Optional[Callable] = None,
    use_mock: bool = False
) -> TaskExecutionEngine:
    """
    Get the singleton instance of the TaskExecutionEngine
    
    Args:
        store_func: Function for storing task data
        retrieve_func: Function for retrieving task data
        use_mock: Whether to use mock mode
        
    Returns:
        TaskExecutionEngine instance
    """
    global _task_execution_engine_instance
    
    if _task_execution_engine_instance is None:
        # Check environment for mock mode
        env_mock = os.environ.get("USE_MOCK_RESPONSES", "False").lower() == "true"
        use_mock = use_mock or env_mock
        
        _task_execution_engine_instance = TaskExecutionEngine(
            store_func=store_func,
            retrieve_func=retrieve_func,
            use_mock=use_mock
        )
    
    return _task_execution_engine_instance