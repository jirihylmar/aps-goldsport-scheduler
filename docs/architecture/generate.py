#!/usr/bin/env python3
"""
GoldSport Scheduler - Architecture Diagram

Generates AWS architecture diagram using Python diagrams library.

Usage:
    python3 docs/architecture/generate.py

Requirements:
    pip3 install --break-system-packages diagrams
    sudo apt-get install -y graphviz

Output:
    docs/architecture/goldsport_scheduler_architecture.png
"""

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import Eventbridge
from diagrams.aws.network import CloudFront
from diagrams.aws.storage import S3
from diagrams.onprem.client import User
from diagrams.programming.language import Python

# Output path relative to script location
SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "goldsport_scheduler_architecture"

# Diagram configuration
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.0",
}

node_attr = {
    "fontsize": "10",
}

edge_attr = {
    "fontsize": "8",
}

with Diagram(
    "Classic Ski School Scheduler",
    filename=str(OUTPUT_FILE),
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # External sources
    external_api = Python("External\nOrders API")
    display = User("Display\nScreen")

    with Cluster("AWS Account (299025166536, eu-central-1)"):

        # Data Acquisition
        with Cluster("Data Acquisition"):
            eventbridge = Eventbridge("EventBridge\n(5 min schedule)")
            fetcher = Lambda("Fetcher\nLambda")

        # Storage
        with Cluster("Storage"):
            input_bucket = S3("Input Bucket\n(orders/)")
            web_bucket = S3("Web Bucket\n(static site)")
            config = S3("Config\n(translations)")
            dynamodb = Dynamodb("DynamoDB\n(schedules)")

        # Processing
        with Cluster("Processing Pipeline"):
            processor = Lambda("Processor\nLambda")

        # Delivery
        cloudfront = CloudFront("CloudFront\nCDN")

    # Data flow
    eventbridge >> Edge(label="trigger") >> fetcher
    external_api >> Edge(label="fetch TSV") >> fetcher
    fetcher >> Edge(label="save") >> input_bucket

    input_bucket >> Edge(label="S3 trigger") >> processor
    processor >> Edge(label="read") >> config
    processor >> Edge(label="store") >> dynamodb
    processor >> Edge(label="generate JSON") >> web_bucket

    web_bucket >> cloudfront
    config >> cloudfront
    cloudfront >> Edge(label="HTTPS") >> display

print(f"Diagram generated: {OUTPUT_FILE}.png")
