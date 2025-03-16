cat > docs/architecture.md <<EOL
# PALIOS-TAEY System Architecture

## Overview
PALIOS-TAEY is an AI-to-AI execution management platform with advanced memory, transcript processing, and multi-model orchestration capabilities. The system routes tasks to the most appropriate AI models based on their capabilities and maintains context through a multi-tier memory system.

## Core Components

### 1. Memory System
The Memory System provides persistent storage across multiple tiers:
- **Ephemeral Memory**: Short-term storage (12 hours)
- **Working Memory**: Medium-term storage (14 days)
- **Reference Memory**: Long-term storage (6 months)
- **Archival Memory**: Permanent storage

### 2. Model Registry
The Model Registry manages the available AI models and their capabilities:
- Tracks model capabilities and confidence scores
- Provides capability discovery mechanism
- Maintains performance history for capability matching

### 3. Task Router
The Task Router directs tasks to the most appropriate model:
- Analyzes task requirements
- Matches tasks to model capabilities
- Provides fallback mechanisms
- Tracks execution performance

### 4. API Gateway
The API Gateway provides external access to PALIOS-TAEY services:
- Handles authentication and authorization
- Provides consistent API interface
- Routes requests to appropriate internal components

### 5. Web Dashboard
The Web Dashboard provides a visual interface to the system:
- Displays system status
- Allows execution of tasks
- Provides access to memory system
- Enables transcript processing

## Data Flow

1. **Task Execution Flow**:
   a. Task submitted via API
   b. Task Router cat > docs/api.md <<EOL
# PALIOS-TAEY API Documentation

## Authentication
All API endpoints (except health check) require authentication using an API key:

\`\`\`
X-API-Key: your_api_key
\`\`\`

For development, use the test key: \`test_key_123\`

## Endpoints

### Health Check
\`GET /health\`

Check system health status.

**Response:**
\`\`\`json
{
  "status": "healthy",
  "version": "1.0.0"
}
\`\`\`

### List Models
\`GET /api/models\`

List available AI models and their capabilities.

**Response:**
\`\`\`json
{
  "models": [
    {
      "model_id": "claude",
      "name": "Claude",
      "description": "Anthropic's Claude large language model",
      "capabilities": {
        "text-generation": {
          "name": "text-generation",
          "description": "Generate high-quality text content",
          "confidence": 0.9
        },
        "reasoning": {
          "name": "reasoning",
          "description": "Complex reasoning and problem-solving",
          "confidence": 0.95
        }
      },
      "available": true
    }
  ]
}
\`\`\`

### Execute Task
\`POST /api/tasks\`

Execute a task using the appropriate AI model.

**Request:**
\`\`\`json
{
  "description": "Summarize the key points from the transcript",
  "model_id": "claude" // Optional - if omitted, best model is selected
}
\`\`\`

**Response:**
\`\`\`json
{
  "task_description": "Summarize the key points from the transcript",
  "analysis": {
    "primary_capability": "summarization",
    "confidence": 0.9,
    "all_capabilities": [
      ["summarization", 0.9],
      ["text-generation", 0.7]
    ]
  },
  "result": {
    "model_used": "claude",
    "capability": "summarization",
    "result": "Summary of key points...",
    "success": true
  },
  "memory_id": "f8a7b6c5-d4e3-f2a1-b0c9-d8a7b6c5d4e3"
}
\`\`\`

### List Memories
\`GET /api/memory\`

List memories from the memory system.

**Query Parameters:**
- \`context_id\`: Memory context (default: "default_context")
- \`limit\`: Maximum number of memories to return (default: 10)

**Response:**
\`\`\`json
{
  "memories": [
    {
      "memory_id": "f8a7b6c5-d4e3-f2a1-b0c9-d8a7b6c5d4e3",
      "content": "Memory content here",
      "context_id": "default_context",
      "tier": "working",
      "metadata": {
        "created_at": "2025-03-14T12:34:56Z",
        "updated_at": "2025-03-14T12:34:56Z",
        "access_count": 0,
        "last_accessed": "2025-03-14T12:34:56Z",
        "type": "transcript"
      }
    }
  ]
}
\`\`\`

### Store Memory
\`POST /api/memory\`

Store a new memory in the memory system.

**Request:**
\`\`\`json
{
  "content": "Memory content to store",
  "context_id": "default_context", // Optional
  "tier": "working", // Optional (ephemeral, working, reference, archival)
  "metadata": { // Optional
    "source": "api",
    "type": "note"
  }
}
\`\`\`

**Response:**
\`\`\`json
{
  "memory_id": "f8a7b6c5-d4e3-f2a1-b0c9-d8a7b6c5d4e3",
  "status": "success"
}
\`\`\`

### Retrieve Memory
\`GET /api/memory/:memory_id\`

Retrieve a specific memory by ID.

**Response:**
\`\`\`json
{
  "memory_id": "f8a7b6c5-d4e3-f2a1-b0c9-d8a7b6c5d4e3",
  "content": "Memory content here",
  "context_id": "default_context",
  "tier": "working",
  "metadata": {
    "created_at": "2025-03-14T12:34:56Z",
    "updated_at": "2025-03-14T12:34:56Z",
    "access_count": 1,
    "last_accessed": "2025-03-14T12:34:56Z",
    "type": "transcript"
  }
}
\`\`\`

### Process Transcript
\`POST /api/transcripts\`

Process a transcript and store it in the memory system.

**Request:**
\`\`\`json
{
  "text": "Transcript text to process",
  "context_id": "default_context" // Optional
}
\`\`\`

**Response:**
\`\`\`json
{
  "processed": true,
  "word_count": 42,
  "memory_id": "f8a7b6c5-d4e3-f2a1-b0c9-d8a7b6c5d4e3",
  "status": "success"
}
\`\`\`
EOLanalyzes requirements
   c. Task Router selects appropriate model
   d. Model executes task
   e. Result stored in Memory System
   f. Result returned to requestor

2. **Memory Storage Flow**:
   a. Content submitted for storage
   b. Tier determined based on context
   c. Memory stored with metadata
   d. Context updated with new memory reference
   e. Expiration set based on tier

3. **Transcript Processing Flow**:
   a. Transcript submitted via API
   b. Transcript analyzed for patterns
   c. Key information extracted
   d. Transcript stored in Memory System
   e. Analysis results returned

## Technical Implementation

### Cloud Infrastructure
- Google Cloud Platform
- Cloud Run for application hosting
- Firestore for Memory System storage
- Artifact Registry for container images

### Application Components
- Python Flask application
- RESTful API design
- Model integrations for Claude and Grok
- Simple web dashboard for visualization
EOL