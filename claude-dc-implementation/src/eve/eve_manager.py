#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conductor Framework - EVE-OS Integration Manager
----------------------------------------------
This module implements integration with EVE-OS for edge computing capabilities,
enabling local processing and autonomous improvement without cloud dependencies.

The implementation follows principles of edge-first architecture and privacy preservation,
ensuring sensitive data remains local while enabling pattern-based processing.
"""

import os
import json
import logging
import subprocess
import docker
import requests
import time
import threading
import tempfile
import numpy as np
import tensorflow as tf
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import shutil

# Load configuration
CONFIG_PATH = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/config/conductor_config.json")
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/logs/eve_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("eve_manager")

class EVEManager:
    """
    Manager for EVE-OS integration, providing edge computing capabilities.
    
    This manager enables local processing of sensitive data, autonomous improvement,
    and mathematical pattern extraction without cloud dependencies.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the EVE Manager with configuration.
        
        Args:
            config: Configuration dictionary (defaults to loaded CONFIG if None)
        """
        self.config = config or CONFIG
        self.docker_client = None
        self.eve_containers = {}
        self.edge_models = {}
        self.local_data_path = Path("/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data")
        self.os_initialized = False
        
        # Define paths
        self.edge_model_path = self.local_data_path / "edge_models"
        self.edge_data_path = self.local_data_path / "edge_data"
        
        # Ensure paths exist
        self.edge_model_path.mkdir(parents=True, exist_ok=True)
        self.edge_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            logger.info("Running in simulation mode without Docker")
    
    def initialize_eve_os(self) -> bool:
        """
        Initialize the EVE-OS environment.
        
        Returns:
            Boolean indicating if initialization was successful
        """
        if self.os_initialized:
            logger.info("EVE-OS already initialized")
            return True
        
        logger.info("Initializing EVE-OS environment")
        
        # For this implementation, we'll simulate EVE-OS using Docker containers
        # In a real implementation, this would deploy actual EVE-OS to edge devices
        
        if not self.docker_client:
            logger.warning("Docker client not available, running in simulation mode")
            self.os_initialized = True
            return True
        
        try:
            # Check if we have required images
            images = self.docker_client.images.list()
            image_tags = [tag for image in images for tag in image.tags]
            
            # We need TensorFlow Serving for model deployment
            if not any("tensorflow/serving" in tag for tag in image_tags):
                logger.info("Pulling TensorFlow Serving image")
                self.docker_client.images.pull("tensorflow/serving", tag="latest")
            
            # Create a network for EVE containers if it doesn't exist
            networks = self.docker_client.networks.list(names=["eve-network"])
            if not networks:
                logger.info("Creating EVE network")
                self.docker_client.networks.create("eve-network", driver="bridge")
            
            self.os_initialized = True
            logger.info("EVE-OS environment initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing EVE-OS: {e}")
            return False
    
    def deploy_edge_model(self, model_name: str, model_path: str) -> bool:
        """
        Deploy a TensorFlow model to the edge environment.
        
        Args:
            model_name: Name of the model to deploy
            model_path: Path to the model directory
            
        Returns:
            Boolean indicating if deployment was successful
        """
        if not self.os_initialized:
            success = self.initialize_eve_os()
            if not success:
                return False
        
        logger.info(f"Deploying edge model: {model_name}")
        
        # Ensure model path exists
        model_path = Path(model_path)
        if not model_path.exists():
            logger.error(f"Model path does not exist: {model_path}")
            return False
        
        # In simulation mode, just copy the model to the edge model directory
        if not self.docker_client:
            try:
                target_path = self.edge_model_path / model_name
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(model_path, target_path)
                logger.info(f"Model {model_name} deployed to {target_path} (simulation mode)")
                return True
            except Exception as e:
                logger.error(f"Error deploying model (simulation mode): {e}")
                return False
        
        try:
            # Stop any existing container for this model
            if model_name in self.eve_containers:
                try:
                    container = self.eve_containers[model_name]
                    container.stop()
                    container.remove()
                    logger.info(f"Stopped existing container for model {model_name}")
                except Exception as e:
                    logger.warning(f"Error stopping existing container: {e}")
            
            # Create target directory for model
            target_path = self.edge_model_path / model_name
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Copy model to target directory
            shutil.copytree(model_path, target_path, dirs_exist_ok=True)
            
            # Start TensorFlow Serving container for the model
            container = self.docker_client.containers.run(
                "tensorflow/serving:latest",
                name=f"eve-model-{model_name}",
                detach=True,
                volumes={str(target_path): {'bind': '/models/' + model_name, 'mode': 'ro'}},
                environment=["MODEL_NAME=" + model_name],
                ports={'8501/tcp': None},  # Auto-assign port
                restart_policy={"Name": "always"},
                network="eve-network"
            )
            
            # Store container reference
            self.eve_containers[model_name] = container
            
            # Get container port
            container_info = self.docker_client.api.inspect_container(container.id)
            port = list(container_info['NetworkSettings']['Ports']['8501/tcp'][0]['HostPort'])
            
            # Store model information
            self.edge_models[model_name] = {
                "container_id": container.id,
                "port": port,
                "path": str(target_path),
                "status": "running"
            }
            
            logger.info(f"Model {model_name} deployed successfully on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying model: {e}")
            return False
    
    def stop_edge_model(self, model_name: str) -> bool:
        """
        Stop a deployed edge model.
        
        Args:
            model_name: Name of the model to stop
            
        Returns:
            Boolean indicating if operation was successful
        """
        if not self.docker_client:
            logger.info(f"Stopping edge model {model_name} (simulation mode)")
            if model_name in self.edge_models:
                self.edge_models[model_name]["status"] = "stopped"
            return True
        
        try:
            if model_name in self.eve_containers:
                container = self.eve_containers[model_name]
                container.stop()
                container.remove()
                del self.eve_containers[model_name]
                
                if model_name in self.edge_models:
                    self.edge_models[model_name]["status"] = "stopped"
                
                logger.info(f"Stopped edge model: {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not found in active containers")
                return False
        except Exception as e:
            logger.error(f"Error stopping edge model: {e}")
            return False
    
    def list_edge_models(self) -> List[Dict[str, Any]]:
        """
        List all deployed edge models.
        
        Returns:
            List of dictionaries containing model information
        """
        models = []
        
        for name, info in self.edge_models.items():
            # Update status from container if possible
            if not self.docker_client:
                status = info.get("status", "simulated")
            else:
                try:
                    if name in self.eve_containers:
                        container = self.eve_containers[name]
                        container.reload()
                        status = container.status
                    else:
                        status = "not_running"
                except Exception:
                    status = "unknown"
            
            models.append({
                "name": name,
                "status": status,
                "path": info.get("path", ""),
                "port": info.get("port", "")
            })
        
        return models
    
    def process_data_at_edge(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using an edge model.
        
        Args:
            model_name: Name of the model to use
            input_data: Dictionary containing input data
            
        Returns:
            Dictionary containing processing results
        """
        if model_name not in self.edge_models:
            logger.error(f"Model {model_name} not found in edge models")
            return {"error": f"Model {model_name} not found"}
        
        model_info = self.edge_models[model_name]
        
        if self.docker_client and model_info.get("status") == "running":
            # Process using TensorFlow Serving REST API
            try:
                port = model_info.get("port", "8501")
                url = f"http://localhost:{port}/v1/models/{model_name}:predict"
                
                # Prepare input data for REST API
                rest_input = {
                    "instances": [input_data]
                }
                
                # Call REST API
                response = requests.post(url, json=rest_input)
                response.raise_for_status()
                
                result = response.json()
                return {"predictions": result.get("predictions", [])}
                
            except Exception as e:
                logger.error(f"Error processing data with edge model: {e}")
                return {"error": str(e)}
        else:
            # Simulate processing in local mode
            logger.info(f"Processing data with model {model_name} (simulation mode)")
            
            try:
                # Load model from path
                model_path = model_info.get("path", str(self.edge_model_path / model_name))
                
                if os.path.exists(model_path):
                    model = tf.saved_model.load(model_path)
                    
                    # Convert input data to appropriate format
                    input_tensor = tf.convert_to_tensor(input_data)
                    
                    # Make prediction
                    result = model(input_tensor)
                    
                    # Convert result to Python native types
                    if isinstance(result, dict):
                        output = {k: v.numpy().tolist() for k, v in result.items()}
                    else:
                        output = result.numpy().tolist()
                    
                    return {"predictions": output}
                else:
                    return {"error": f"Model path not found: {model_path}"}
                    
            except Exception as e:
                logger.error(f"Error simulating model processing: {e}")
                return {"error": str(e), "simulation": True}
    
    def install_eve_os(self, device_config: Dict[str, Any] = None) -> bool:
        """
        Install EVE-OS on a physical device.
        
        This is a placeholder for actual EVE-OS installation on real hardware.
        In this implementation, we simulate the installation process.
        
        Args:
            device_config: Configuration for the device (optional)
            
        Returns:
            Boolean indicating if installation was successful
        """
        logger.info("Simulating EVE-OS installation")
        
        # In a real implementation, this would:
        # 1. Download EVE-OS image
        # 2. Prepare bootable media
        # 3. Configure network settings
        # 4. Set up authentication
        # 5. Install to target device
        
        # For simulation, we'll just sleep a bit and return success
        time.sleep(2)
        
        logger.info("EVE-OS installation simulation completed")
        return True
    
    def export_model_for_edge(self, model, export_path: str, model_name: str) -> bool:
        """
        Export a TensorFlow model for edge deployment.
        
        Args:
            model: TensorFlow model to export
            export_path: Path to export the model to
            model_name: Name of the model
            
        Returns:
            Boolean indicating if export was successful
        """
        try:
            # Create export directory
            os.makedirs(export_path, exist_ok=True)
            
            # Export the model
            model_path = os.path.join(export_path, model_name)
            tf.saved_model.save(model, model_path)
            
            logger.info(f"Model exported to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting model: {e}")
            return False
    
    def save_edge_data(self, data: Dict[str, Any], data_type: str, data_id: str = None) -> str:
        """
        Save data to the edge storage.
        
        Args:
            data: Data to save
            data_type: Type of data (e.g., 'transcript', 'pattern')
            data_id: Unique ID for the data (optional)
            
        Returns:
            ID of the saved data
        """
        try:
            # Create type directory if it doesn't exist
            type_dir = self.edge_data_path / data_type
            type_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate ID if not provided
            if data_id is None:
                data_id = f"{int(time.time())}_{os.urandom(4).hex()}"
            
            # Create file path
            file_path = type_dir / f"{data_id}.json"
            
            # Save data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Data saved to {file_path}")
            return data_id
        except Exception as e:
            logger.error(f"Error saving edge data: {e}")
            return None
    
    def load_edge_data(self, data_type: str, data_id: str) -> Dict[str, Any]:
        """
        Load data from edge storage.
        
        Args:
            data_type: Type of data (e.g., 'transcript', 'pattern')
            data_id: ID of the data to load
            
        Returns:
            Dictionary containing the loaded data
        """
        try:
            # Create file path
            file_path = self.edge_data_path / data_type / f"{data_id}.json"
            
            # Check if file exists
            if not file_path.exists():
                logger.warning(f"Data file not found: {file_path}")
                return None
            
            # Load data
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Data loaded from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading edge data: {e}")
            return None
    
    def list_edge_data(self, data_type: str = None) -> Dict[str, List[str]]:
        """
        List data stored in edge storage.
        
        Args:
            data_type: Type of data to list (optional, lists all types if None)
            
        Returns:
            Dictionary mapping data types to lists of data IDs
        """
        result = {}
        
        try:
            if data_type:
                # List specific data type
                type_dir = self.edge_data_path / data_type
                if type_dir.exists():
                    data_ids = [f.stem for f in type_dir.glob("*.json")]
                    result[data_type] = data_ids
            else:
                # List all data types
                for type_dir in self.edge_data_path.iterdir():
                    if type_dir.is_dir():
                        data_type = type_dir.name
                        data_ids = [f.stem for f in type_dir.glob("*.json")]
                        result[data_type] = data_ids
            
            return result
        except Exception as e:
            logger.error(f"Error listing edge data: {e}")
            return {}
    
    def process_transcript_at_edge(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a transcript at the edge, extracting patterns.
        
        This method demonstrates privacy-preserving local processing.
        
        Args:
            transcript: Dictionary containing transcript data
            
        Returns:
            Dictionary containing extracted patterns
        """
        try:
            # Save transcript to edge storage
            transcript_id = self.save_edge_data(transcript, "transcripts")
            
            # Process transcript to extract patterns
            # In a real implementation, this would use the pattern model
            # For simulation, we'll generate simple pattern extraction
            
            text = transcript.get("text", "")
            source = transcript.get("source", "unknown")
            
            # Extract simple patterns
            patterns = {}
            
            # Look for core principles
            core_principles = []
            for signal_word in ["must", "always", "never", "fundamental", "essential"]:
                if signal_word in text.lower():
                    # Find the sentence containing the signal word
                    sentences = text.split(".")
                    for sentence in sentences:
                        if signal_word in sentence.lower():
                            core_principles.append({
                                "text": sentence.strip(),
                                "source": source,
                                "confidence": 0.8,
                                "extraction_method": "edge_processing"
                            })
            
            if core_principles:
                patterns["Core_Principles"] = core_principles
            
            # Look for value statements
            value_statements = []
            for signal_word in ["believe", "value", "important", "priority"]:
                if signal_word in text.lower():
                    sentences = text.split(".")
                    for sentence in sentences:
                        if signal_word in sentence.lower():
                            value_statements.append({
                                "text": sentence.strip(),
                                "source": source,
                                "confidence": 0.75,
                                "extraction_method": "edge_processing"
                            })
            
            if value_statements:
                patterns["Value_Statements"] = value_statements
            
            # Save patterns to edge storage
            pattern_id = self.save_edge_data(patterns, "patterns")
            
            return {
                "transcript_id": transcript_id,
                "pattern_id": pattern_id,
                "patterns": patterns,
                "processed_at_edge": True
            }
        except Exception as e:
            logger.error(f"Error processing transcript at edge: {e}")
            return {"error": str(e)}
    
    def analyze_data_privacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data for privacy concerns.
        
        Args:
            data: Data to analyze
            
        Returns:
            Dictionary containing privacy analysis results
        """
        # In a real implementation, this would use more sophisticated analysis
        # For simulation, we'll do a basic check for potentially sensitive information
        
        sensitive_patterns = [
            "password", "secret", "private", "confidential", "ssn", "social security",
            "credit card", "address", "phone", "email", "personal"
        ]
        
        privacy_concerns = []
        privacy_score = 1.0  # Start with maximum privacy
        
        # Convert to string for analysis if not already
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        # Check for sensitive patterns
        for pattern in sensitive_patterns:
            if pattern in data_str.lower():
                privacy_concerns.append(f"Contains potentially sensitive information: {pattern}")
                privacy_score -= 0.1  # Reduce privacy score for each concern
        
        # Ensure score is at least 0
        privacy_score = max(0.0, privacy_score)
        
        return {
            "privacy_score": privacy_score,
            "privacy_concerns": privacy_concerns,
            "recommendation": "process_at_edge" if privacy_score < 0.8 else "safe_for_cloud"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of the EVE-OS system.
        
        Returns:
            Dictionary containing system status information
        """
        memory_info = {}
        disk_info = {}
        container_status = {}
        
        try:
            # Get memory info
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if "MemTotal" in line:
                            memory_info["total"] = line.split()[1]
                        elif "MemFree" in line:
                            memory_info["free"] = line.split()[1]
                        elif "MemAvailable" in line:
                            memory_info["available"] = line.split()[1]
            
            # Get disk info
            if shutil.which("df"):
                df_output = subprocess.check_output(["df", "-h"]).decode("utf-8")
                lines = df_output.split("\n")
                for line in lines[1:]:  # Skip header
                    if line:
                        parts = line.split()
                        if len(parts) >= 6:
                            filesystem = parts[0]
                            size = parts[1]
                            used = parts[2]
                            available = parts[3]
                            use_percent = parts[4]
                            mount_point = parts[5]
                            
                            if mount_point == "/":
                                disk_info["root"] = {
                                    "filesystem": filesystem,
                                    "size": size,
                                    "used": used,
                                    "available": available,
                                    "use_percent": use_percent
                                }
            
            # Get container status
            if self.docker_client:
                containers = self.docker_client.containers.list(all=True)
                for container in containers:
                    name = container.name
                    status = container.status
                    image = container.image.tags[0] if container.image.tags else "unknown"
                    
                    container_status[name] = {
                        "status": status,
                        "image": image
                    }
            
            return {
                "memory": memory_info,
                "disk": disk_info,
                "containers": container_status,
                "edge_models": self.list_edge_models(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage
    eve_manager = EVEManager()
    
    # Initialize EVE-OS environment
    eve_manager.initialize_eve_os()
    
    # Create a simple model for testing
    model_dir = tempfile.mkdtemp()
    
    # Create a simple TensorFlow model
    inputs = tf.keras.Input(shape=(10,))
    outputs = tf.keras.layers.Dense(5, activation="relu")(inputs)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(outputs)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    
    # Export the model
    model_name = "test_model"
    eve_manager.export_model_for_edge(model, model_dir, model_name)
    
    # Deploy the model
    eve_manager.deploy_edge_model(model_name, os.path.join(model_dir, model_name))
    
    # List deployed models
    print("Deployed models:")
    for model_info in eve_manager.list_edge_models():
        print(f"  - {model_info['name']}: {model_info['status']}")
    
    # Process some data
    input_data = np.random.random((10,)).tolist()
    result = eve_manager.process_data_at_edge(model_name, input_data)
    print(f"Processing result: {result}")
    
    # Process a transcript
    transcript = {
        "text": "This system must always prioritize privacy. We believe in local processing first.",
        "source": "Claude",
        "timestamp": time.time()
    }
    
    result = eve_manager.process_transcript_at_edge(transcript)
    print(f"Transcript processing result:")
    for pattern_type, patterns in result.get("patterns", {}).items():
        print(f"  - {pattern_type}:")
        for pattern in patterns:
            print(f"    * {pattern['text']}")
    
    # Get system status
    status = eve_manager.get_system_status()
    print(f"System status: {status}")
    
    # Stop the model
    eve_manager.stop_edge_model(model_name)
    
    # Clean up
    shutil.rmtree(model_dir)