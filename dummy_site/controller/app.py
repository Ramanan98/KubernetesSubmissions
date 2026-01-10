import logging
import os
import sys
import time

import requests
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logger = logging.getLogger("dummysite-controller")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

if os.environ.get("KUBERNETES_SERVICE_HOST"):
    config.load_incluster_config()
else:
    config.load_kube_config()

core_v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()

GROUP = "stable.dwk"
VERSION = "v1"
PLURAL = "dummysites"
GATEWAY_NAME = "dummysite-gateway"
GATEWAY_NAMESPACE = "default"


def fetch_website_html(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def create_pod(name, namespace, html_content):
    import base64

    encoded_html = base64.b64encode(html_content.encode()).decode()
    pod = client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=client.V1ObjectMeta(
            name=f"{name}-pod",
            namespace=namespace,
            labels={"app": name, "dummysite": name},
        ),
        spec=client.V1PodSpec(
            containers=[
                client.V1Container(
                    name="server",
                    image="python:3.11-alpine",
                    command=[
                        "python",
                        "-c",
                        f"""
import http.server
import socketserver
import base64

html = base64.b64decode("{encoded_html}").decode()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", 80), Handler) as httpd:
    httpd.serve_forever()
""",
                    ],
                    ports=[client.V1ContainerPort(container_port=80)],
                )
            ]
        ),
    )
    try:
        core_v1.create_namespaced_pod(namespace=namespace, body=pod)
        logger.info(f"Created Pod {name}-pod in namespace {namespace}")
    except ApiException as e:
        if e.status == 409:
            core_v1.delete_namespaced_pod(name=f"{name}-pod", namespace=namespace)
            time.sleep(2)
            core_v1.create_namespaced_pod(namespace=namespace, body=pod)
            logger.info(f"Recreated Pod {name}-pod in namespace {namespace}")
        else:
            raise


def create_service(name, namespace):
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=f"{name}-svc", namespace=namespace, labels={"dummysite": name}
        ),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=80, target_port=80)],
        ),
    )
    try:
        core_v1.create_namespaced_service(namespace=namespace, body=service)
        logger.info(f"Created Service {name}-svc in namespace {namespace}")
    except ApiException as e:
        if e.status != 409:
            raise


def create_httproute(name, namespace):
    httproute = {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "HTTPRoute",
        "metadata": {
            "name": f"{name}-route",
            "namespace": namespace,
            "labels": {"dummysite": name},
        },
        "spec": {
            "parentRefs": [{"name": GATEWAY_NAME, "namespace": GATEWAY_NAMESPACE}],
            "rules": [
                {
                    "matches": [{"path": {"type": "PathPrefix", "value": "/"}}],
                    "backendRefs": [{"name": f"{name}-svc", "port": 80}],
                }
            ],
        },
    }
    try:
        custom_api.create_namespaced_custom_object(
            group="gateway.networking.k8s.io",
            version="v1",
            namespace=namespace,
            plural="httproutes",
            body=httproute,
        )
        logger.info(f"Created HTTPRoute {name}-route in namespace {namespace}")
    except ApiException as e:
        if e.status != 409:
            raise


def delete_resources(name, namespace):
    try:
        core_v1.delete_namespaced_pod(name=f"{name}-pod", namespace=namespace)
        logger.info(f"Deleted Pod {name}-pod")
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Error deleting pod: {e}")

    try:
        core_v1.delete_namespaced_service(name=f"{name}-svc", namespace=namespace)
        logger.info(f"Deleted Service {name}-svc")
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Error deleting service: {e}")

    try:
        custom_api.delete_namespaced_custom_object(
            group="gateway.networking.k8s.io",
            version="v1",
            namespace=namespace,
            plural="httproutes",
            name=f"{name}-route",
        )
        logger.info(f"Deleted HTTPRoute {name}-route")
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Error deleting httproute: {e}")


def handle_dummysite(event_type, obj):
    name = obj["metadata"]["name"]
    namespace = obj["metadata"].get("namespace", "default")
    website_url = obj.get("spec", {}).get("website_url", "")

    logger.info(f"Event: {event_type} for DummySite {name} in namespace {namespace}")

    if event_type == "ADDED" or event_type == "MODIFIED":
        html_content = fetch_website_html(website_url)
        if html_content:
            create_pod(name, namespace, html_content)
            create_service(name, namespace)
            create_httproute(name, namespace)
        else:
            logger.error(f"Failed to fetch HTML from {website_url}")
    elif event_type == "DELETED":
        delete_resources(name, namespace)


def main():
    logger.info("Starting DummySite controller...")
    w = watch.Watch()

    while True:
        try:
            logger.info("Watching for DummySite resources...")
            for event in w.stream(
                custom_api.list_cluster_custom_object,
                group=GROUP,
                version=VERSION,
                plural=PLURAL,
            ):
                event_type = event["type"]
                obj = event["object"]
                handle_dummysite(event_type, obj)
        except ApiException as e:
            logger.error(f"API Exception: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
