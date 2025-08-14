# KubeSeek Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Application](#running-the-application)
5. [Using the Dashboard](#using-the-dashboard)
6. [API Integration](#api-integration)
7. [Monitoring Scenarios](#monitoring-scenarios)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)
10. [Best Practices](#best-practices)

## Quick Start

### Prerequisites
- Python 3.7 or higher
- Access to a Kubernetes cluster
- `kubectl` configured and working

### 1. Install Dependencies
```bash
pip install flask kubernetes requests
```

### 2. Start the Services
```bash
# Terminal 1: Start the monitoring backend
python monitor_cluster.py

# Terminal 2: Start the web dashboard
python app.py
```

### 3. Access the Dashboard
Open your browser and navigate to: `http://127.0.0.1:5002/dashboard`

## Installation

### Step-by-Step Installation

#### 1. Clone or Download the Project
```bash
git clone <repository-url>
cd kubeseek
```

#### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note:** If no requirements.txt exists, install manually:
```bash
pip install flask kubernetes requests
```

#### 4. Verify Kubernetes Access
```bash
kubectl get nodes
kubectl get namespaces
```

### Docker Installation (Alternative)

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install flask kubernetes requests

EXPOSE 5001 5002

CMD ["python", "monitor_cluster.py"]
```

#### 2. Build and Run
```bash
docker build -t kubeseek .
docker run -p 5001:5001 -p 5002:5002 kubeseek
```

## Configuration

### Kubernetes Configuration

#### In-Cluster Deployment
When running inside Kubernetes, the application automatically uses in-cluster configuration:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubeseek-monitor
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubeseek-monitor
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "namespaces"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubeseek-monitor
subjects:
- kind: ServiceAccount
  name: kubeseek-monitor
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: kubeseek-monitor
  apiGroup: rbac.authorization.k8s.io
```

#### Local Development
For local development, ensure your `kubeconfig` is properly configured:

```bash
# Check current context
kubectl config current-context

# List available contexts
kubectl config get-contexts

# Switch context if needed
kubectl config use-context <context-name>
```

### Application Configuration

#### Environment Variables
```bash
# Optional: Override default ports
export KUBESEEK_BACKEND_PORT=5001
export KUBESEEK_DASHBOARD_PORT=5002

# Optional: Set log level
export KUBESEEK_LOG_LEVEL=INFO
```

#### Logging Configuration
The application logs to both console and file (`kubeseek.log`):

```python
# Customize logging in monitor_cluster.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('kubeseek.log')
    ]
)
```

## Running the Application

### Development Mode

#### 1. Start Backend Service
```bash
python monitor_cluster.py
```

**Expected Output:**
```
2024-01-01 10:00:00 [INFO] Starting KubeSeek using Kubernetes Python client
2024-01-01 10:00:00 [INFO] Starting monitoring loop
2024-01-01 10:00:00 [INFO] Fetching namespaces
2024-01-01 10:00:00 [INFO] Fetching nodes
2024-01-01 10:00:00 [INFO] Cluster monitoring cycle complete
 * Running on http://0.0.0.0:5001
```

#### 2. Start Dashboard Service
```bash
python app.py
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5002
 * Debug mode: off
```

#### 3. Verify Services
```bash
# Check backend health
curl http://127.0.0.1:5001/health

# Check dashboard
curl http://127.0.0.1:5002/dashboard
```

### Production Mode

#### Using Gunicorn
```bash
# Install Gunicorn
pip install gunicorn

# Start backend with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 monitor_cluster:app

# Start dashboard with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

#### Using Systemd (Linux)
Create service files:

**Backend Service (`/etc/systemd/system/kubeseek-backend.service`):**
```ini
[Unit]
Description=KubeSeek Backend Service
After=network.target

[Service]
Type=simple
User=kubeseek
WorkingDirectory=/opt/kubeseek
ExecStart=/opt/kubeseek/venv/bin/python monitor_cluster.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Dashboard Service (`/etc/systemd/system/kubeseek-dashboard.service`):**
```ini
[Unit]
Description=KubeSeek Dashboard Service
After=network.target

[Service]
Type=simple
User=kubeseek
WorkingDirectory=/opt/kubeseek
ExecStart=/opt/kubeseek/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and Start Services:**
```bash
sudo systemctl enable kubeseek-backend
sudo systemctl enable kubeseek-dashboard
sudo systemctl start kubeseek-backend
sudo systemctl start kubeseek-dashboard
```

## Using the Dashboard

### Dashboard Overview

The KubeSeek dashboard provides a real-time view of your Kubernetes cluster health:

#### 1. Header Section
- **Title:** "Kubernetes Monitoring Dashboard" with heartbeat icon
- **Refresh Button:** Manual refresh with sync icon

#### 2. Nodes Section
- **Icon:** Server icon
- **Display:** Grid of node cards
- **Status Indicators:**
  - 🟢 Green: Healthy nodes
  - 🔴 Red: Unhealthy nodes

#### 3. Namespaces Section
- **Icon:** Layer group icon
- **Display:** Grid of namespace cards
- **Status Indicators:**
  - 🟢 Green: Healthy namespaces
  - 🔴 Red: Unhealthy namespaces with error details

### Interacting with the Dashboard

#### Manual Refresh
Click the "Refresh" button to immediately update the dashboard with the latest cluster status.

#### Status Interpretation
- **Healthy (Green):** All resources are functioning normally
- **Unhealthy (Red):** Issues detected that require attention

#### Error Details
For unhealthy namespaces, additional information is displayed:
- List of unhealthy pods
- Log error indicators

### Dashboard Features

#### Responsive Design
- **Desktop:** Multi-column grid layout
- **Mobile:** Single-column layout for better readability
- **Large Screens:** Optimized spacing and sizing

#### Dark Theme
- Optimized for monitoring environments
- Reduces eye strain during extended use
- Professional appearance

## API Integration

### REST API Endpoints

#### Health Check API
```bash
# Get comprehensive health information
curl http://127.0.0.1:5001/health

# Get namespace status only
curl http://127.0.0.1:5001/status
```

#### Response Format
```json
{
  "nodes": {
    "worker-node-1": {
      "status": 200,
      "message": "Ready"
    }
  },
  "namespaces": {
    "client-app": {
      "status": 200,
      "message": "Namespace is healthy",
      "unhealthy_pods": []
    }
  }
}
```

### Python Integration Examples

#### Basic Health Check
```python
import requests
import json

def check_cluster_health():
    try:
        response = requests.get("http://127.0.0.1:5001/health")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error checking cluster health: {e}")
        return None

# Usage
health_data = check_cluster_health()
if health_data:
    print(f"Nodes: {len(health_data['nodes'])}")
    print(f"Namespaces: {len(health_data['namespaces'])}")
```

#### Health Monitoring Script
```python
import requests
import time
import smtplib
from email.mime.text import MIMEText

def monitor_cluster_health():
    while True:
        try:
            response = requests.get("http://127.0.0.1:5001/health")
            health_data = response.json()
            
            # Check for unhealthy nodes
            unhealthy_nodes = [
                node for node, status in health_data["nodes"].items()
                if status["status"] != 200
            ]
            
            # Check for unhealthy namespaces
            unhealthy_namespaces = [
                ns for ns, status in health_data["namespaces"].items()
                if status["status"] != 200
            ]
            
            if unhealthy_nodes or unhealthy_namespaces:
                send_alert(unhealthy_nodes, unhealthy_namespaces)
                
        except Exception as e:
            print(f"Monitoring error: {e}")
            
        time.sleep(300)  # Check every 5 minutes

def send_alert(unhealthy_nodes, unhealthy_namespaces):
    # Implementation for sending alerts
    pass

# Start monitoring
monitor_cluster_health()
```

#### Integration with Existing Monitoring
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
            "healthy_namespaces": sum(1 for s in health_data["namespaces"].values() if s["status"] == 200),
            "health_percentage": calculate_health_percentage(health_data)
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_health_percentage(health_data):
    total_resources = len(health_data["nodes"]) + len(health_data["namespaces"])
    healthy_resources = (
        sum(1 for s in health_data["nodes"].values() if s["status"] == 200) +
        sum(1 for s in health_data["namespaces"].values() if s["status"] == 200)
    )
    return (healthy_resources / total_resources * 100) if total_resources > 0 else 0

if __name__ == "__main__":
    app.run(port=5003)
```

### Webhook Integration
```python
import requests
import json

def send_webhook_alert(webhook_url, health_data):
    unhealthy_nodes = [
        node for node, status in health_data["nodes"].items()
        if status["status"] != 200
    ]
    
    unhealthy_namespaces = [
        ns for ns, status in health_data["namespaces"].items()
        if status["status"] != 200
    ]
    
    if unhealthy_nodes or unhealthy_namespaces:
        payload = {
            "text": "🚨 Kubernetes Cluster Health Alert",
            "attachments": [
                {
                    "color": "#ff0000",
                    "fields": [
                        {
                            "title": "Unhealthy Nodes",
                            "value": ", ".join(unhealthy_nodes) if unhealthy_nodes else "None",
                            "short": True
                        },
                        {
                            "title": "Unhealthy Namespaces",
                            "value": ", ".join(unhealthy_namespaces) if unhealthy_namespaces else "None",
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        requests.post(webhook_url, json=payload)
```

## Monitoring Scenarios

### Scenario 1: Development Environment Monitoring

#### Setup
```bash
# Start monitoring for development cluster
python monitor_cluster.py &
python app.py &
```

#### Usage
- Monitor development namespaces (client-*)
- Quick health checks during development
- Immediate feedback on deployment issues

### Scenario 2: Production Cluster Monitoring

#### Setup
```bash
# Deploy as Kubernetes service
kubectl apply -f kubeseek-deployment.yaml
```

#### Usage
- Continuous monitoring of production cluster
- Integration with existing alerting systems
- Historical health tracking

### Scenario 3: Multi-Cluster Monitoring

#### Setup
```python
# Multi-cluster configuration
clusters = {
    "dev": "http://dev-cluster:5001/health",
    "staging": "http://staging-cluster:5001/health",
    "prod": "http://prod-cluster:5001/health"
}

def monitor_all_clusters():
    for cluster_name, url in clusters.items():
        try:
            response = requests.get(url)
            health_data = response.json()
            print(f"{cluster_name}: {len(health_data['nodes'])} nodes, {len(health_data['namespaces'])} namespaces")
        except Exception as e:
            print(f"Error monitoring {cluster_name}: {e}")
```

### Scenario 4: CI/CD Integration

#### GitHub Actions Example
```yaml
name: Cluster Health Check
on:
  push:
    branches: [main]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
    - name: Check cluster health
      run: |
        response=$(curl -s http://127.0.0.1:5001/health)
        unhealthy_count=$(echo $response | jq '.nodes | map(select(.status != 200)) | length + .namespaces | map(select(.status != 200)) | length')
        if [ $unhealthy_count -gt 0 ]; then
          echo "Cluster has $unhealthy_count unhealthy resources"
          exit 1
        fi
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Kubernetes Connection Issues

**Problem:** Cannot connect to Kubernetes cluster
```bash
Error: Failed to get pods in client-app: (403)
```

**Solutions:**
```bash
# Check kubeconfig
kubectl config current-context

# Verify cluster access
kubectl get nodes

# Check RBAC permissions
kubectl auth can-i get nodes
kubectl auth can-i get pods --all-namespaces
```

#### 2. Service Not Starting

**Problem:** Flask app fails to start
```bash
Error: Address already in use
```

**Solutions:**
```bash
# Check if ports are in use
netstat -tulpn | grep :5001
netstat -tulpn | grep :5002

# Kill existing processes
sudo lsof -ti:5001 | xargs kill -9
sudo lsof -ti:5002 | xargs kill -9
```

#### 3. Dashboard Not Loading

**Problem:** Dashboard shows error or blank page

**Solutions:**
```bash
# Check backend service
curl http://127.0.0.1:5001/health

# Check dashboard service
curl http://127.0.0.1:5002/dashboard

# Check logs
tail -f kubeseek.log
```

#### 4. No Namespaces Showing

**Problem:** Dashboard shows no namespaces

**Solutions:**
```bash
# Check if namespaces exist
kubectl get namespaces | grep client

# Verify namespace naming convention
# Only namespaces starting with "client" are monitored
```

#### 5. High Resource Usage

**Problem:** Application consuming too much CPU/memory

**Solutions:**
```python
# Adjust monitoring interval in monitor_cluster.py
time.sleep(120)  # Change from 60 to 120 seconds

# Reduce log analysis scope
# Comment out log checking in process_pod function
```

### Debug Mode

#### Enable Debug Logging
```python
# In monitor_cluster.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('kubeseek.log')]
)
```

#### Verbose Output
```bash
# Run with verbose output
python -u monitor_cluster.py 2>&1 | tee kubeseek.log
```

### Performance Monitoring

#### Monitor Application Performance
```bash
# Check CPU and memory usage
top -p $(pgrep -f monitor_cluster.py)

# Monitor network connections
netstat -an | grep :5001
```

## Advanced Usage

### Custom Monitoring Rules

#### Add Custom Health Checks
```python
def custom_health_check(namespace: str):
    """Custom health check for specific requirements"""
    try:
        # Add your custom logic here
        pods = v1.list_namespaced_pod(namespace=namespace).items
        
        # Example: Check for specific labels
        critical_pods = [
            pod for pod in pods
            if pod.metadata.labels.get('critical') == 'true'
        ]
        
        return {
            "status": 200 if len(critical_pods) > 0 else 500,
            "message": f"Found {len(critical_pods)} critical pods",
            "critical_pods": [pod.metadata.name for pod in critical_pods]
        }
    except Exception as e:
        return {"status": 500, "message": str(e)}
```

#### Custom Log Analysis
```python
import re

def custom_log_analysis(logs: str):
    """Custom log analysis patterns"""
    patterns = [
        r"ERROR.*database.*connection",
        r"WARN.*memory.*usage",
        r"CRITICAL.*service.*down"
    ]
    
    issues = []
    for pattern in patterns:
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            issues.extend(matches)
    
    return issues
```

### Metrics Collection

#### Prometheus Integration
```python
from prometheus_client import Counter, Gauge, Histogram
import time

# Define metrics
health_check_total = Counter('kubeseek_health_checks_total', 'Total health checks')
unhealthy_resources = Gauge('kubeseek_unhealthy_resources', 'Number of unhealthy resources')
health_check_duration = Histogram('kubeseek_health_check_duration_seconds', 'Health check duration')

def monitored_health_check(namespace: str):
    start_time = time.time()
    try:
        result = check_namespace_health(namespace)
        health_check_total.inc()
        
        if result["status"] != 200:
            unhealthy_resources.inc()
        
        return result
    finally:
        health_check_duration.observe(time.time() - start_time)
```

### Alerting Integration

#### Slack Integration
```python
import requests

def send_slack_alert(webhook_url, message):
    payload = {
        "text": message,
        "username": "KubeSeek Bot",
        "icon_emoji": ":warning:"
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")

# Usage in monitoring loop
if unhealthy_nodes:
    send_slack_alert(
        webhook_url,
        f"🚨 Unhealthy nodes detected: {', '.join(unhealthy_nodes)}"
    )
```

#### Email Alerts
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(smtp_server, smtp_port, username, password, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email alert: {e}")
```

## Best Practices

### Security Best Practices

#### 1. RBAC Configuration
```yaml
# Minimal required permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubeseek-monitor
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "namespaces"]
  verbs: ["get", "list"]
```

#### 2. Network Security
```bash
# Use HTTPS in production
# Configure firewall rules
# Implement authentication
```

#### 3. Resource Limits
```yaml
# Kubernetes deployment with resource limits
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

### Performance Best Practices

#### 1. Monitoring Interval
- Adjust based on cluster size and requirements
- Balance between responsiveness and resource usage
- Consider different intervals for different resource types

#### 2. Log Analysis
- Limit log analysis to critical containers
- Use efficient regex patterns
- Implement log rotation

#### 3. Caching
- Cache Kubernetes API responses when appropriate
- Implement request deduplication
- Use connection pooling

### Operational Best Practices

#### 1. Monitoring the Monitor
```python
# Health check for the monitoring service itself
@app.route("/monitor-health")
def monitor_health():
    return jsonify({
        "status": "healthy",
        "uptime": time.time() - start_time,
        "last_check": last_check_time
    })
```

#### 2. Graceful Shutdown
```python
import signal
import sys

def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    # Cleanup code here
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

#### 3. Configuration Management
```python
import os
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    return {
        "monitoring_interval": int(os.getenv("MONITORING_INTERVAL", "60")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "timeout": int(os.getenv("TIMEOUT", "30"))
    }
```

### Maintenance Best Practices

#### 1. Regular Updates
- Keep dependencies updated
- Monitor for security vulnerabilities
- Test updates in staging environment

#### 2. Backup and Recovery
- Backup configuration files
- Document deployment procedures
- Test recovery procedures

#### 3. Documentation
- Keep documentation updated
- Document custom configurations
- Maintain runbooks for common issues