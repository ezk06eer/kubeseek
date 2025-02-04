import subprocess
import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from flask import Flask, jsonify
import threading
import time
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kubeseek.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
status_data = []
node_health = {}
namespace_status = {}


@app.route("/status", methods=["GET"])
def get_status():
    """Endpoint to get the current status of namespaces."""
    logger.info("GET request received for /status endpoint")
    response = { "namespaces": namespace_status }
    return jsonify(response)


@app.route("/health", methods=["GET"])
def get_health():
    """Endpoint to get the health of nodes and namespaces."""
    logger.info("GET request received for /health endpoint")
    response = {
        "nodes": node_health,
        "namespaces": namespace_status
    }
    return jsonify(response)


def run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    logger.debug(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr.strip()}")
            raise RuntimeError(f"Command failed: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


def get_namespaces():
    """Get all namespaces starting with 'client'."""
    logger.info("Fetching namespaces")
    try:
        output = run_kubectl_command(["kubectl", "get", "namespaces", "-o", "jsonpath={.items[*].metadata.name}"])
        namespaces = [ns for ns in output.split() if ns.startswith("client")]
        logger.debug(f"Found namespaces: {namespaces}")
        return namespaces
    except Exception as e:
        logger.error(f"Error fetching namespaces: {str(e)}")
        return []


def get_pods(namespace):
    """Get all pods in a namespace that are not in the 'Succeeded' phase."""
    logger.debug(f"Fetching pods for namespace: {namespace}")
    try:
        output = run_kubectl_command(
            ["kubectl", "get", "pods", "-n", namespace,
             "--field-selector=status.phase!=Succeeded",
             "-o", "jsonpath={.items[*].metadata.name}"]
        )
        pods = output.split()
        logger.debug(f"Found {len(pods)} pods in namespace {namespace}")
        return pods
    except Exception as e:
        logger.error(f"Error fetching pods for namespace {namespace}: {str(e)}")
        return []


def get_nodes():
    """Get all nodes in the cluster."""
    logger.info("Fetching nodes")
    try:
        output = run_kubectl_command(["kubectl", "get", "nodes", "-o", "jsonpath={.items[*].metadata.name}"])
        nodes = output.split()
        logger.debug(f"Found nodes: {nodes}")
        return nodes
    except Exception as e:
        logger.error(f"Error fetching nodes: {str(e)}")
        return []


def check_logs(namespace, pod, command):
    """Check logs for a specific pod using a command."""
    logger.debug(f"Checking logs for {namespace}/{pod} with command: {command}")
    try:
        output = run_kubectl_command(["kubectl", "exec", "-n", namespace, pod, "--"] + command.split())
        return output.strip()
    except Exception as e:
        logger.warning(f"Failed to check logs for {namespace}/{pod}: {str(e)}")
        return str(e)


def check_node_health(node):
    """Check the health of a node."""
    logger.info(f"Checking health for node: {node}")
    try:
        output = run_kubectl_command(["kubectl", "get", "node", node, "-o", "json"])
        node_info = json.loads(output)
        conditions = node_info["status"]["conditions"]
        ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)

        if ready_condition and ready_condition["status"] == "True":
            logger.info(f"Node {node} is healthy")
            return {"status": 200, "message": "Node is healthy"}
        else:
            logger.warning(f"Node {node} is not ready")
            return {"status": 500, "message": "Node is not ready"}
    except Exception as e:
        logger.error(f"Error checking node health for {node}: {str(e)}")
        return {"status": 500, "message": str(e)}


def check_namespace_health(namespace):
    """Check the health of a namespace by verifying pod statuses and logs."""
    logger.info(f"Checking health for namespace: {namespace}")
    try:
        # Check for pods in failed states
        output = run_kubectl_command([
            "kubectl", "get", "pods", "-n", namespace,
            "--field-selector=status.phase!=Running,status.phase!=Succeeded",
            "-o", "json"
        ])
        pod_info = json.loads(output)

        if len(pod_info.get("items", [])) > 0:
            unhealthy_pods = [pod["metadata"]["name"] for pod in pod_info["items"]]
            logger.warning(f"Namespace {namespace} has unhealthy pods: {unhealthy_pods}")
            return {
                "status": 502,
                "message": "Some pods are not in a healthy state",
                "unhealthy_pods": unhealthy_pods
            }

        # Check logs of running pods
        pods = get_pods(namespace)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_pod, repeat(namespace), pods))

        # Collect pods with log issues
        log_issues = [result for result in results if result is not None]
        if log_issues:
            unhealthy_pods = [issue["pod"] for issue in log_issues]
            logger.warning(f"Namespace {namespace} has pods with log errors: {unhealthy_pods}")
            return {
                "status": 502,
                "message": "Some pods have errors in logs",
                "unhealthy_pods": unhealthy_pods,
                "log_issues": log_issues
            }

        logger.info(f"Namespace {namespace} is healthy")
        return {"status": 200, "message": "Namespace is healthy"}

    except Exception as e:
        logger.error(f"Error checking namespace health for {namespace}: {str(e)}")
        return {"status": 500, "message": str(e)}


def process_pod(namespace, pod):
    """Process a pod to check for issues in logs."""
    logger.debug(f"Processing pod {pod} in namespace {namespace}")
    try:
        # Verify pod is actually running
        status = run_kubectl_command([
            "kubectl", "get", "pod", "-n", namespace, pod,
            "-o", "jsonpath={.status.phase}"
        ])
        if status != "Running":
            logger.debug(f"Skipping non-running pod: {namespace}/{pod} ({status})")
            return None

        issues = []

        # Check dmesg logs
        dmesg_logs = check_logs(namespace, pod, "dmesg -T")
        error_pattern = r"oom|failed|critical|server 127\.0\.0\.1 not responding, timed out"
        filtered_dmesg = "\n".join(
            line for line in dmesg_logs.split("\n")
            if re.search(error_pattern, line, re.IGNORECASE) and "GPT" not in line
        )
        if filtered_dmesg:
            logger.info(f"Found dmesg issues in {namespace}/{pod}")
            issues.append({"source": "dmesg", "logs": filtered_dmesg.split("\n")})

        # Check celery logs for non-Redis pods
        if "redis" not in pod.lower():
            celery_logs = check_logs(namespace, pod, "tail -n10 /home/faraday/.faraday/logs/celery.log")
            if re.search(r"oom|111|timeout", celery_logs, re.IGNORECASE):
                filtered_celery = "\n".join(
                    line for line in celery_logs.split("\n")
                    if re.search(r"oom|111|timeout", line, re.IGNORECASE)
                )
                logger.info(f"Found celery.log issues in {namespace}/{pod}")
                issues.append({"source": "celery.log", "logs": filtered_celery.split("\n")})

        if issues:
            return {
                "namespace": namespace,
                "pod": pod,
                "issues": issues
            }
        return None

    except Exception as e:
        logger.error(f"Error processing pod {namespace}/{pod}: {str(e)}")
        return None


def monitor_cluster():
    """Monitor the cluster and update status data."""
    logger.info("Starting cluster monitoring thread")
    global status_data, node_health, namespace_status

    while True:
        try:
            logger.info("Starting monitoring cycle")
            data = []
            namespaces = get_namespaces()
            nodes = get_nodes()

            # Check node health
            with ThreadPoolExecutor() as executor:
                node_health = dict(zip(nodes, executor.map(check_node_health, nodes)))

            # Check namespace health (now includes log checking)
            with ThreadPoolExecutor() as executor:
                namespace_status = dict(zip(namespaces, executor.map(check_namespace_health, namespaces)))

            # Process pods for detailed status data
            with ThreadPoolExecutor() as executor:
                for namespace in namespaces:
                    pods = get_pods(namespace)
                    results = executor.map(process_pod, repeat(namespace), pods)
                    data.extend(filter(None, results))

            status_data = data
            logger.info("Completed monitoring cycle")
            time.sleep(60)

        except Exception as e:
            logger.critical(f"Critical error in monitoring thread: {str(e)}")
            logger.error(traceback.format_exc())
            time.sleep(60)


def start_monitoring():
    """Start the monitoring thread."""
    logger.info("Initializing monitoring thread")
    monitoring_thread = threading.Thread(target=monitor_cluster, daemon=True)
    monitoring_thread.start()


if __name__ == "__main__":
    logger.info("Starting KubeSeek application")
    start_monitoring()
    app.run(host="0.0.0.0", port=5001)
