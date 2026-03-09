from fastmcp import FastMCP # like FastAPI, but for AI.
from kubernetes import client, config
import os

# Initialize the MCP Server
mcp = FastMCP("IncidentCommander")


def get_k8s_client():
    """Helper to detect if we have a real K8s connection."""
    try:
        config.load_kube_config()
        return client.CoreV1Api()
    except Exception:
        # If no cluster is found, we'll return None to trigger 'Mock Mode'
        return None


@mcp.tool()
def scan_cluster_health(namespace: str = "default") -> str:
    """
    Checks the status of all pods in a namespace.
    Use this first when an incident is reported.
    """
    v1 = get_k8s_client()

    # MOCK MODE: So you can test this even without a real K8s cluster
    if not v1:
        return "⚠️ [MOCK] Found 1 unhealthy pod: 'payment-processor-v1' (Status: CrashLoopBackOff)"

    try:
        pods = v1.list_namespaced_pod(namespace)
        unhealthy = [f"{p.metadata.name}" for p in pods.items if p.status.phase != "Running"]

        if not unhealthy:
            return f"✅ All pods in '{namespace}' are healthy."
        return f"⚠️ Unhealthy pods: {', '.join(unhealthy)}"
    except Exception as e:
        return f"❌ K8s API Error: {str(e)}"

@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = "default", tail_lines: int = 50) -> str:
    """
    Fetches the last N lines of logs from a specific pod.
    Use this to perform Root Cause Analysis (RCA) when a pod is crashing or slow.
    """
    v1 = get_k8s_client()

    # MOCK MODE: Returns a fake error for testing logic
    if not v1:
        if "payment" in pod_name:
            return "ERROR: Connection refused to database at 10.0.1.45:5432. Retrying in 5s..."
        return f"Log output for {pod_name}: [Standard output stream is empty]"

    try:
        # The 'kubernetes' client makes this a single line of code
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
        return logs
    except Exception as e:
        return f"❌ Error fetching logs for {pod_name}: {str(e)}"


if __name__ == "__main__":
    mcp.run()