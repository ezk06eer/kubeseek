from flask import Flask, jsonify
from kubernetes import client, config
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import time
import re

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('kubeseek.log')]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Shared state
status_data = []
node_health = {}
namespace_status = {}

# Kubernetes setup
try:
    config.load_incluster_config()
except:
    config.load_kube_config()
v1 = client.CoreV1Api()

@app.route("/status")
def get_status():
    logger.info("GET /status")
    return jsonify(namespace_status)

@app.route("/health")
def get_health():
    logger.info("GET /health")
    return jsonify({"nodes": node_health, "namespaces": namespace_status})

def get_namespaces():
    logger.info("Fetching namespaces")
    return [
        ns.metadata.name for ns in v1.list_namespace().items
        if ns.metadata.name.startswith("client")
    ]

def get_nodes():
    logger.info("Fetching nodes")
    return [node.metadata.name for node in v1.list_node().items]

def get_pods(namespace: str):
    try:
        return [
            pod.metadata.name for pod in v1.list_namespaced_pod(
                namespace=namespace
            ).items if pod.status.phase != "Succeeded"
        ]
    except Exception as e:
        logger.warning(f"Failed to get pods in {namespace}: {e}")
        return []

def check_node_health(node: str):
    try:
        node_obj = v1.read_node_status(node)
        for condition in node_obj.status.conditions:
            if condition.type == "Ready":
                return {"status": 200 if condition.status == "True" else 500, "message": condition.reason}
    except Exception as e:
        return {"status": 500, "message": str(e)}

def check_namespace_health(namespace: str):
    try:
        pods = v1.list_namespaced_pod(namespace=namespace).items
        unhealthy = [
            pod.metadata.name for pod in pods
            if pod.status.phase not in ("Running", "Succeeded")
        ]
        return {
            "status": 200 if not unhealthy else 500,
            "message": "Namespace is healthy" if not unhealthy else "Some pods are unhealthy",
            "unhealthy_pods": unhealthy or []
        }
    except Exception as e:
        return {"status": 500, "message": str(e)}

def check_logs(namespace: str, pod: str, container: str, command: list):
    try:
        return v1.read_namespaced_pod_log(
            name=pod,
            namespace=namespace,
            container=container,
            tail_lines=100,
            _preload_content=True
        )
    except Exception as e:
        return str(e)

def process_pod(namespace: str, pod_name: str):
    logger.info(f"Processing pod {namespace}/{pod_name}")
    try:
        pod = v1.read_namespaced_pod(pod_name, namespace)
        if pod.status.phase == "Succeeded":
            return None

        issues = []
        containers = [c.name for c in pod.spec.containers]

        for container in containers:
            log = check_logs(namespace, pod_name, container, [])
            dmesg_lines = [
                line for line in log.splitlines()
                if re.search(r"oom|failed|critical", line, re.IGNORECASE) and "GPT" not in line
            ]
            if dmesg_lines:
                issues.append({"source": "dmesg", "logs": dmesg_lines})

            if "redis" not in pod_name.lower():
                celery_logs = [
                    line for line in log.splitlines()
                    if re.search(r"111", line) and "CPendingDeprecationWarning" not in line
                ]
                if celery_logs:
                    issues.append({"source": "celery.log", "logs": celery_logs})

        if issues:
            return {"namespace": namespace, "pod": pod_name, "issues": issues}
        return None
    except Exception as e:
        logger.error(f"Error in pod {namespace}/{pod_name}: {e}")
        return None

def monitor_cluster():
    global status_data, node_health, namespace_status
    logger.info("Starting monitoring loop")

    while True:
        try:
            namespaces = get_namespaces()
            nodes = get_nodes()

            with ThreadPoolExecutor() as executor:
                node_health.update(dict(zip(nodes, executor.map(check_node_health, nodes))))
                namespace_status.update(dict(zip(namespaces, executor.map(check_namespace_health, namespaces))))

                all_results = []
                for ns in namespaces:
                    pods = get_pods(ns)
                    results = list(executor.map(lambda p: process_pod(ns, p), pods))
                    all_results.extend(filter(None, results))

            status_data = all_results
            logger.info("Cluster monitoring cycle complete")
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
        time.sleep(60)

def start_monitoring():
    threading.Thread(target=monitor_cluster, daemon=True).start()

if __name__ == "__main__":
    logger.info("Starting KubeSeek using Kubernetes Python client")
    start_monitoring()
    app.run(host="0.0.0.0", port=5001)
