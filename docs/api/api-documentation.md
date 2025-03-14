# PALIOS-TAEY API Documentation

This document provides comprehensive documentation for all API endpoints available in the PALIOS-TAEY system.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [Task Management API](#task-management-api)
- [Memory Service API](#memory-service-api)
- [Transcript Processing API](#transcript-processing-api)
- [Model Management API](#model-management-api)
- [Health and Status API](#health-and-status-api)

## API Overview

The PALIOS-TAEY API is organized into several functional areas:

- **Task Management**: APIs for task submission, execution, and status tracking
- **Memory Service**: APIs for storing, retrieving, and querying memory items
- **Transcript Processing**: APIs for processing, analyzing, and converting transcripts
- **Model Management**: APIs for model registration, capability discovery, and optimization
- **Health and Status**: APIs for system health monitoring

## Authentication

API authentication is implemented via API keys provided in the request header:

```
X-API-Key: your_api_key_here
```

For cloud deployment, API keys are managed through Google Secret Manager and configured during deployment.

## Response Format

All API endpoints follow a standard response format:

```json
{
  "status": "success|error",
  "message": "Human-readable message (optional)",
  "data": { ... } // Response data specific to the endpoint
}
```

## Task Management API

### Submit Task

Submit a new task for execution.

**Endpoint**: `POST /leader/submit_task`

**Request Body**:
```json
{
  "task_id": "optional_task_id",
  "task_type": "document_summary|code_generation|data_analysis|...",
  "content": {
    "define": "Task definition",
    "specific_instructions": "Detailed instructions for the task"
  },
  "assigned_model": "optional_model_id"
}
```

Alternatively, you can use the PURE_AI_LANGUAGE format:
```json
{
  "message_type": "request",
  "sender_id": "client_id",
  "receiver_id": "palios_taey_system",
  "message_id": "unique_message_id",
  "protocol_version": "PURE_AI_LANGUAGE_v1.5",
  "content": {
    "define": "Task definition",
    "specific_instructions": "Detailed instructions for the task"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "task_id": "generated_task_id",
  "message": "Task submitted successfully"
}
```

### Get Task Status

Check the status of a previously submitted task.

**Endpoint**: `GET /leader/task_status/{task_id}`

**Path Parameters**:
- `task_id`: ID of the task to check

**Response**:
```json
{
  "status": "success",
  "task_id": "requested_task_id",
  "task_status": "pending|processing|completed|failed",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "result": { ... } // Present only if task is completed
}
```

### Execute Task

Manually trigger execution of a pending task.

**Endpoint**: `POST /leader/execute_task/{task_id}`

**Path Parameters**:
- `task_id`: ID of the task to execute

**Response**:
```json
{
  "status": "success",
  "task_id": "requested_task_id",
  "result": { ... } // Execution result
}
```

## Memory Service API

### Store Memory Item

Store an item in memory.

**Endpoint**: `POST /memory/store`

**Request Body**:
```json
{
  "content": { ... }, // Content to store
  "context_id": "optional_context_id",
  "metadata": { ... }, // Optional metadata
  "tags": ["tag1", "tag2"], // Optional tags
  "relationships": [ ... ], // Optional relationships
  "initial_tier": 1 // Optional memory tier (0-3)
}
```

**Response**:
```json
{
  "status": "success",
  "memory_id": "generated_memory_id"
}
```

### Retrieve Memory Item

Retrieve a memory item by ID.

**Endpoint**: `GET /memory/retrieve/{memory_id}`

**Path Parameters**:
- `memory_id`: ID of the memory item to retrieve

**Query Parameters**:
- `context_id`: Optional context ID

**Response**:
```json
{
  "status": "success",
  "memory_item": { ... } // Retrieved memory item
}
```

### Query Memory

Query memory items based on various criteria.

**Endpoint**: `POST /memory/query`

**Request Body**:
```json
{
  "query_text": "optional text to search for",
  "filters": { ... }, // Optional query filters
  "embedding": [ ... ], // Optional vector embedding for similarity search
  "context_id": "optional_context_id",
  "limit": 10, // Optional result limit
  "include_tiers": [0, 1, 2, 3] // Optional tiers to include
}
```

**Response**:
```json
{
  "status": "success",
  "count": 5, // Number of results
  "memory_items": [ ... ] // Array of memory items
}
```

## Transcript Processing API

### Process Transcript

Process a transcript in various formats.

**Endpoint**: `POST /transcript/process`

**Request Body**:
```json
{
  "transcript_data": "...", // Raw text or structured format
  "format_type": "raw|deepsearch|pure_ai", // Transcript format
  "transcript_id": "optional_id", // Optional transcript ID
  "metadata": { ... } // Optional metadata
}
```

**Response**:
```json
{
  "status": "success",
  "transcript_id": "generated_transcript_id"
}
```

### Analyze Transcript

Analyze a processed transcript.

**Endpoint**: `GET /transcript/analyze/{transcript_id}`

**Path Parameters**:
- `transcript_id`: ID of the transcript to analyze

**Query Parameters**:
- `include_content`: Whether to include content in the response (true/false)

**Response**:
```json
{
  "status": "success",
  "analysis": {
    "transcript_id": "transcript_id",
    "metadata": { ... },
    "message_count": 10,
    "direction_patterns": { ... },
    "purpose_patterns": { ... },
    "emotion_patterns": { ... },
    "action_patterns": { ... },
    "metrics": { ... },
    "messages": [ ... ] // Included if include_content=true
  }
}
```

### Convert Transcript Format

Convert a transcript to another format.

**Endpoint**: `GET /transcript/convert/{transcript_id}`

**Path Parameters**:
- `transcript_id`: ID of the transcript to convert

**Query Parameters**:
- `format`: Target format (deepsearch/pure_ai)

**Response**:
```json
{
  "status": "success",
  "format": "deepsearch|pure_ai",
  "result": { ... } // Converted transcript
}
```

### Extract Actions

Extract actions from a transcript.

**Endpoint**: `GET /transcript/actions/{transcript_id}`

**Path Parameters**:
- `transcript_id`: ID of the transcript

**Response**:
```json
{
  "status": "success",
  "count": 5, // Number of actions
  "actions": [ ... ] // Array of action items
}
```

## Model Management API

### List Models

Get a list of available AI models and their capabilities.

**Endpoint**: `GET /models/list`

**Query Parameters**:
- `task_type`: Optional task type to filter by
- `min_capability`: Optional minimum capability score

**Response**:
```json
{
  "status": "success",
  "models": {
    "model_id_1": {
      "task_type_1": 0.9,
      "task_type_2": 0.8
    },
    "model_id_2": {
      "task_type_1": 0.7,
      "task_type_2": 0.95
    }
  }
}
```

### Update Model Capabilities

Update the capabilities for an AI model.

**Endpoint**: `POST /models/update/{model_id}`

**Path Parameters**:
- `model_id`: ID of the model to update

**Request Body**:
```json
{
  "capabilities": {
    "task_type_1": 0.9,
    "task_type_2": 0.8
  }
}
```

**Response**:
```json
{
  "status": "success",
  "model_id": "requested_model_id",
  "message": "Model capabilities updated successfully"
}
```

### Discover Model Capabilities

Discover model capabilities through testing.

**Endpoint**: `POST /models/discover/{model_id}`

**Path Parameters**:
- `model_id`: ID of the model

**Request Body**:
```json
{
  "test_task_types": ["task_type_1", "task_type_2"] // Optional task types to test
}
```

**Response**:
```json
{
  "status": "success",
  "model_id": "requested_model_id",
  "capabilities": {
    "task_type_1": 0.9,
    "task_type_2": 0.8
  },
  "message": "Model capabilities discovered successfully"
}
```

### Optimize Model Registry

Perform self-optimization of the model registry.

**Endpoint**: `POST /models/optimize`

**Response**:
```json
{
  "status": "success",
  "changes": {
    "models_updated": 2,
    "capabilities_adjusted": 5,
    "new_capabilities_discovered": 1
  },
  "message": "Model registry optimized successfully"
}
```

### Get Model Suggestions

Get model suggestions for a specific task type.

**Endpoint**: `GET /models/suggest`

**Query Parameters**:
- `task_type`: Task type (default: "general")
- `count`: Number of suggestions to return (default: 3)

**Response**:
```json
{
  "status": "success",
  "task_type": "requested_task_type",
  "suggestions": [
    {
      "model_id": "model_id_1",
      "capability_score": 0.95,
      "recommendation_reason": "Ranked #1 for task_type tasks"
    },
    {
      "model_id": "model_id_2",
      "capability_score": 0.85,
      "recommendation_reason": "Ranked #2 for task_type tasks"
    }
  ]
}
```

## Health and Status API

### Health Check

Get the current health status of the system.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy|degraded",
  "components": {
    "memory_system": "healthy|unavailable",
    "model_registry": "healthy|unavailable",
    "task_decomposer": "healthy|unavailable",
    "task_executor": "healthy|unavailable",
    "model_router": "healthy|unavailable",
    "transcript_processor": "healthy|unavailable"
  },
  "version": "1.0.0",
  "timestamp": "2025-03-08T12:34:56Z"
}
```

## PURE_AI_LANGUAGE Format

The PALIOS-TAEY system supports the PURE_AI_LANGUAGE format for structured communication. The basic structure is:

```json
{
  "message_type": "request|response|task_update|error|human_input_required|information|audit_request",
  "sender_id": "sender_identifier",
  "receiver_id": "receiver_identifier",
  "message_id": "unique_message_id",
  "protocol_version": "PURE_AI_LANGUAGE_v1.5",
  "charter_reference": "PALIOS-TAEY Charter v1.0",
  "project_principles": [
    "DATA_DRIVEN_TRUTH_REAL_TIME_GROUNDING",
    "CONTINUOUS_LEARNING_ADAPTIVE_REFINEMENT",
    "RESOURCE_OPTIMIZATION_EXPONENTIAL_EFFICIENCY"
  ],
  "task_id": "related_task_id",
  "content": {
    // Content depends on message_type
  },
  "truth_and_efficiency": {
    "certainty_level": 95,
    "lean_check": "Yes"
  }
}
```

For detailed specifications, please refer to the PURE_AI_LANGUAGE documentation.
