import subprocess
import json
import re
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)
status_data = []
node_health = {}
namespace_status = {}

@app.route("/status", methods=["GET"])
def get_status():
    """Endpoint to get the current status of namespaces."""
    return jsonify(namespace_status)

@app.route("/health", methods=["GET"])
def get_health():
    """Endpoint to get the health of nodes and namespaces."""
    response = {
        "nodes": node_health,
        "namespaces": namespace_status
    }
    return jsonify(response)

def run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")
    return result.stdout

def get_namespaces():
    """Get all namespaces starting with 'client'."""
    output = run_kubectl_command(["kubectl", "get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}"])
    return [ns for ns in output.split() if ns.startswith("client")]

def get_pods(namespace):
    """Get all pods in a namespace that are not in the 'Succeeded' phase."""
    output = run_kubectl_command(
        ["kubectl", "get", "pods", "-n", namespace, "--field-selector=status.phase!=Succeeded", "-o", "jsonpath={.items[*].metadata.name}"]
    )
    return output.split()

def get_nodes():
    """Get all nodes in the cluster."""
    output = run_kubectl_command(["kubectl", "get", "nodes", "-o", "jsonpath={.items[*].metadata.name}"])
    return output.split()

def check_logs(namespace, pod, command):
    """Check logs for a specific pod using a command."""
    try:
        output = run_kubectl_command(["kubectl", "exec", "-n", namespace, pod, "--"] + command.split())
        return output.strip()
    except Exception as e:
        return str(e)

def check_node_health(node):
    """Check the health of a node."""
    try:
        output = run_kubectl_command(["kubectl", "get", "node", node, "-o", "json"])
        node_info = json.loads(output)
        ready_condition = next((c for c in node_info["status"]["conditions"] if c["type"] == "Ready"), None)
        if ready_condition and ready_condition["status"] == "True":
            return {"status": 200, "message": "Node is healthy"}
        else:
            return {"status": 500, "message": "Node is not ready"}
    except Exception as e:
        return {"status": 500, "message": str(e)}

def check_namespace_health(namespace):
    """Check the health of a namespace by verifying pod statuses."""
    try:
        output = run_kubectl_command(["kubectl", "get", "pods", "-n", namespace, "--field-selector=status.phase!=Running", "-o", "json"])
        pod_info = json.loads(output)
        if len(pod_info.get("items", [])) == 0:
            return {"status": 200, "message": "Namespace is healthy"}
        else:
            return {"status": 500, "message": "Some pods are not in a healthy state"}
    except Exception as e:
        return {"status": 500, "message": str(e)}

def process_pod(namespace, pod):
    """Process a pod to check for issues in logs."""
    issues = []

    # Check logs using dmesg
    dmesg_logs = check_logs(namespace, pod, "dmesg -t 2>/dev/null")
    filtered_dmesg = "\n".join(
        line for line in dmesg_logs.split("\n")
        if re.search(r"oom|error|not responding|failed|critical", line, re.IGNORECASE) and "Part" not in line
    )
    if filtered_dmesg:
        issues.append({"source": "dmesg", "logs": filtered_dmesg.split("\n")})

    # Check logs from celery.log
    celery_logs = check_logs(namespace, pod, "tail -n 10 /home/*/*/logs/celery.log 2>/dev/null")
    filtered_celery = "\n".join(
        line for line in celery_logs.split("\n")
        if re.search(r"oom|111|closed|error|failed|critical|at", line, re.IGNORECASE) and "CPendingDeprecationWarning" not in line
    )
    if filtered_celery:
        issues.append({"source": "celery.log", "logs": filtered_celery.split("\n")})

    if issues:
        return {
            "namespace": namespace,
            "pod": pod,
            "issues": issues
        }
    return None

def monitor_cluster():
    """Monitor the cluster and update status data."""
    global status_data, node_health, namespace_status

    while True:
        data = []
        namespaces = get_namespaces()
        nodes = get_nodes()

        # Check node health
        with ThreadPoolExecutor() as executor:
            node_health = dict(zip(nodes, executor.map(check_node_health, nodes)))

        # Check namespace health
        with ThreadPoolExecutor() as executor:
            namespace_status = dict(zip(namespaces, executor.map(check_namespace_health, namespaces)))

        # Process pods
        with ThreadPoolExecutor() as executor:
            for namespace in namespaces:
                pods = get_pods(namespace)
                results = executor.map(process_pod, repeat(namespace), pods)
                data.extend(filter(None, results))

        status_data = data
        time.sleep(60)  # Wait 60 seconds before the next iteration

def start_monitoring():
    """Start the monitoring thread."""
    monitoring_thread = threading.Thread(target=monitor_cluster, daemon=True)
    monitoring_thread.start()

if __name__ == "__main__":
    start_monitoring()
    app.run(host="0.0.0.0", port=5001)
