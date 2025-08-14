# KubeSeek API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Backend API (monitor_cluster.py)](#backend-api-monitor_clusterpy)
3. [Web Dashboard API (app.py)](#web-dashboard-api-apppy)
4. [Core Functions](#core-functions)
5. [Data Structures](#data-structures)
6. [Configuration](#configuration)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Overview

KubeSeek is a Kubernetes monitoring tool that provides real-time health monitoring for nodes and namespaces in a Kubernetes cluster. The system consists of two main components:

- **Backend Service** (`monitor_cluster.py`): Monitors the cluster and exposes REST APIs
- **Web Dashboard** (`app.py`): Provides a web interface for viewing cluster health

## Backend API (monitor_cluster.py)

### Base URL
```
http://127.0.0.1:5001
```

### Endpoints

#### GET /health
Returns comprehensive health information for all nodes and namespaces.

**Response Format:**
```json
{
  "nodes": {
    "node-name": {
      "status": 200,
      "message": "Ready"
    }
  },
  "namespaces": {
    "namespace-name": {
      "status": 200,
      "message": "Namespace is healthy",
      "unhealthy_pods": []
    }
  }
}
```

**Example Response:**
```json
{
  "nodes": {
    "worker-node-1": {
      "status": 200,
      "message": "Ready"
    },
    "worker-node-2": {
      "status": 500,
      "message": "NotReady"
    }
  },
  "namespaces": {
    "client-app": {
      "status": 200,
      "message": "Namespace is healthy",
      "unhealthy_pods": []
    },
    "client-api": {
      "status": 500,
      "message": "Some pods are unhealthy",
      "unhealthy_pods": ["api-pod-1", "api-pod-2"]
    }
  }
}
```

**Status Codes:**
- `200`: Healthy/Ready
- `500`: Unhealthy/Not Ready

#### GET /status
Returns namespace status information only.

**Response Format:**
```json
{
  "namespace-name": {
    "status": 200,
    "message": "Namespace is healthy",
    "unhealthy_pods": []
  }
}
```

## Web Dashboard API (app.py)

### Base URL
```
http://127.0.0.1:5002
```

### Endpoints

#### GET /dashboard
Renders the main monitoring dashboard HTML page.

**Query Parameters:** None

**Response:** HTML page with cluster health information

**Example Usage:**
```bash
curl http://127.0.0.1:5002/dashboard
```

## Core Functions

### Kubernetes Interaction Functions

#### `get_namespaces()`
Retrieves all namespaces that start with "client".

**Returns:** `List[str]` - List of namespace names

**Example:**
```python
namespaces = get_namespaces()
# Returns: ['client-app', 'client-api', 'client-db']
```

#### `get_nodes()`
Retrieves all node names in the cluster.

**Returns:** `List[str]` - List of node names

**Example:**
```python
nodes = get_nodes()
# Returns: ['master-node', 'worker-node-1', 'worker-node-2']
```

#### `get_pods(namespace: str)`
Retrieves all pod names in a specific namespace, excluding completed pods.

**Parameters:**
- `namespace` (str): The namespace to query

**Returns:** `List[str]` - List of pod names

**Example:**
```python
pods = get_pods("client-app")
# Returns: ['app-pod-1', 'app-pod-2', 'app-pod-3']
```

### Health Check Functions

#### `check_node_health(node: str)`
Checks the health status of a specific node.

**Parameters:**
- `node` (str): The name of the node to check

**Returns:** `Dict[str, Any]` - Health status information

**Example:**
```python
health = check_node_health("worker-node-1")
# Returns: {"status": 200, "message": "Ready"}
```

#### `check_namespace_health(namespace: str)`
Checks the health status of all pods in a namespace.

**Parameters:**
- `namespace` (str): The name of the namespace to check

**Returns:** `Dict[str, Any]` - Namespace health information

**Example:**
```python
health = check_namespace_health("client-app")
# Returns: {
#   "status": 200,
#   "message": "Namespace is healthy",
#   "unhealthy_pods": []
# }
```

### Log Analysis Functions

#### `check_logs(namespace: str, pod: str, container: str, command: list)`
Retrieves logs from a specific container in a pod.

**Parameters:**
- `namespace` (str): The namespace containing the pod
- `pod` (str): The name of the pod
- `container` (str): The name of the container
- `command` (list): Command arguments (unused in current implementation)

**Returns:** `str` - Container logs (last 100 lines)

**Example:**
```python
logs = check_logs("client-app", "app-pod-1", "app-container", [])
# Returns: "2024-01-01 10:00:00 INFO Application started..."
```

#### `process_pod(namespace: str, pod_name: str)`
Analyzes a pod for potential issues by checking container logs.

**Parameters:**
- `namespace` (str): The namespace containing the pod
- `pod_name` (str): The name of the pod to analyze

**Returns:** `Dict[str, Any]` or `None` - Issues found or None if no issues

**Example:**
```python
issues = process_pod("client-app", "app-pod-1")
# Returns: {
#   "namespace": "client-app",
#   "pod": "app-pod-1",
#   "issues": [
#     {
#       "source": "dmesg",
#       "logs": ["Out of memory error detected"]
#     }
#   ]
# }
```

### Monitoring Functions

#### `monitor_cluster()`
Main monitoring loop that continuously checks cluster health.

**Behavior:**
- Runs in an infinite loop
- Checks all nodes and namespaces every 60 seconds
- Updates global state variables
- Uses ThreadPoolExecutor for parallel processing

**Global State Updates:**
- `status_data`: List of pod issues found
- `node_health`: Dictionary of node health statuses
- `namespace_status`: Dictionary of namespace health statuses

#### `start_monitoring()`
Starts the monitoring loop in a background thread.

**Usage:**
```python
start_monitoring()
# Monitoring begins in background thread
```

## Data Structures

### Node Health Status
```python
{
  "status": int,      # 200 for healthy, 500 for unhealthy
  "message": str      # Status description (e.g., "Ready", "NotReady")
}
```

### Namespace Health Status
```python
{
  "status": int,              # 200 for healthy, 500 for unhealthy
  "message": str,             # Status description
  "unhealthy_pods": List[str] # List of unhealthy pod names
}
```

### Pod Issue Structure
```python
{
  "namespace": str,           # Namespace name
  "pod": str,                 # Pod name
  "issues": [
    {
      "source": str,          # Issue source ("dmesg" or "celery.log")
      "logs": List[str]       # Relevant log lines
    }
  ]
}
```

## Configuration

### Kubernetes Configuration
The application automatically detects Kubernetes configuration:
1. First tries in-cluster configuration (when running inside Kubernetes)
2. Falls back to kubeconfig file (when running locally)

### Logging Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('kubeseek.log')]
)
```

### Flask Configuration
- **Backend Service**: Runs on `0.0.0.0:5001`
- **Web Dashboard**: Runs on `0.0.0.0:5002`

## Error Handling

### API Error Responses
All API endpoints return appropriate HTTP status codes:
- `200`: Success
- `500`: Internal server error

### Exception Handling
The application includes comprehensive exception handling:
- Kubernetes API errors are caught and logged
- Network errors are handled gracefully
- Individual pod/container failures don't stop the entire monitoring process

### Log Error Detection
The system automatically detects specific error patterns:
- **dmesg errors**: OOM, failed, critical (excluding GPT-related messages)
- **Celery errors**: Lines containing "111" (excluding CPendingDeprecationWarning)

## Examples

### Starting the Services

1. **Start the backend monitoring service:**
```bash
python monitor_cluster.py
```

2. **Start the web dashboard:**
```bash
python app.py
```

### API Usage Examples

#### Check Cluster Health
```bash
curl http://127.0.0.1:5001/health
```

#### Get Namespace Status Only
```bash
curl http://127.0.0.1:5001/status
```

#### Access Web Dashboard
```bash
curl http://127.0.0.1:5002/dashboard
```

### Python Client Example
```python
import requests

# Get health information
response = requests.get("http://127.0.0.1:5001/health")
health_data = response.json()

# Check node status
for node, status in health_data["nodes"].items():
    if status["status"] != 200:
        print(f"Node {node} is unhealthy: {status['message']}")

# Check namespace status
for namespace, status in health_data["namespaces"].items():
    if status["status"] != 200:
        print(f"Namespace {namespace} has issues: {status['message']}")
        if status["unhealthy_pods"]:
            print(f"Unhealthy pods: {', '.join(status['unhealthy_pods'])}")
```

### Integration Example
```python
from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/cluster-summary")
def cluster_summary():
    try:
        response = requests.get("http://127.0.0.1:5001/health")
        health_data = response.json()
        
        summary = {
            "total_nodes": len(health_data["nodes"]),
            "healthy_nodes": sum(1 for s in health_data["nodes"].values() if s["status"] == 200),
            "total_namespaces": len(health_data["namespaces"]),
            "healthy_namespaces": sum(1 for s in health_data["namespaces"].values() if s["status"] == 200)
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5003)
```

## Dependencies

### Required Python Packages
- `flask`: Web framework
- `kubernetes`: Kubernetes Python client
- `requests`: HTTP client library
- `concurrent.futures`: Threading utilities

### Installation
```bash
pip install flask kubernetes requests
```

## Security Considerations

1. **Kubernetes RBAC**: Ensure the service account has appropriate permissions
2. **Network Security**: Consider using HTTPS in production
3. **Authentication**: Add authentication for production deployments
4. **Resource Limits**: Monitor resource usage of the monitoring service

## Troubleshooting

### Common Issues

1. **Kubernetes Connection Errors**
   - Verify kubeconfig is properly configured
   - Check cluster accessibility
   - Ensure proper RBAC permissions

2. **Missing Namespaces**
   - Only namespaces starting with "client" are monitored
   - Check namespace naming convention

3. **High Resource Usage**
   - Adjust monitoring interval (currently 60 seconds)
   - Consider reducing log analysis scope

4. **Dashboard Not Loading**
   - Verify both services are running
   - Check firewall settings
   - Ensure ports 5001 and 5002 are accessible