"""Copy a Neo4j database from the source configured in .env.

Defaults:
  source: SOURCE_NEO4J_URI / SOURCE_NEO4J_USER / SOURCE_NEO4J_PASSWORD
          or NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
  target: bolt://localhost:7687 / neo4j / password

Optional target env vars:
  TARGET_NEO4J_URI
  TARGET_NEO4J_USER
  TARGET_NEO4J_PASSWORD
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

BATCH_SIZE = int(os.getenv("NEO4J_COPY_BATCH_SIZE", "500"))
COPY_ID_PROP = "__source_element_id__"


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def quote_name(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def labels_clause(labels: list[str]) -> str:
    if not labels:
        return ""
    return ":" + ":".join(quote_name(label) for label in labels)


def props_literal(props: dict[str, Any], prefix: str = "props") -> str:
    if not props:
        return ""
    return ", ".join(f"{quote_name(key)}: ${prefix}.{key}" for key in props)


def connect(uri: str, user: str, password: str):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def count_source(source_driver) -> tuple[int, int]:
    with source_driver.session() as session:
        node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
    return node_count, rel_count


def clear_target(target_driver) -> None:
    with target_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n").consume()


def copy_nodes(source_driver, target_driver) -> int:
    copied = 0
    while True:
        with source_driver.session() as session:
            records = list(
                session.run(
                    """
                    MATCH (n)
                    RETURN elementId(n) AS source_id,
                           labels(n) AS labels,
                           properties(n) AS props
                    ORDER BY elementId(n)
                    SKIP $skip LIMIT $limit
                    """,
                    skip=copied,
                    limit=BATCH_SIZE,
                )
            )

        if not records:
            return copied

        with target_driver.session() as session:
            for record in records:
                props = dict(record["props"])
                props[COPY_ID_PROP] = record["source_id"]
                query = f"CREATE (n{labels_clause(record['labels'])} {{{props_literal(props)}}})"
                session.run(query, props=props).consume()

        copied += len(records)
        print(f"Copied nodes: {copied}")


def copy_relationships(source_driver, target_driver) -> int:
    copied = 0
    while True:
        with source_driver.session() as session:
            records = list(
                session.run(
                    """
                    MATCH (a)-[r]->(b)
                    RETURN elementId(a) AS start_id,
                           elementId(b) AS end_id,
                           type(r) AS type,
                           properties(r) AS props
                    ORDER BY elementId(r)
                    SKIP $skip LIMIT $limit
                    """,
                    skip=copied,
                    limit=BATCH_SIZE,
                )
            )

        if not records:
            return copied

        with target_driver.session() as session:
            for record in records:
                props = dict(record["props"])
                rel_type = quote_name(record["type"])
                rel_props = props_literal(props)
                rel_body = f" {{{rel_props}}}" if rel_props else ""
                session.run(
                    f"""
                    MATCH (a {{{quote_name(COPY_ID_PROP)}: $start_id}})
                    MATCH (b {{{quote_name(COPY_ID_PROP)}: $end_id}})
                    CREATE (a)-[r:{rel_type}{rel_body}]->(b)
                    """,
                    start_id=record["start_id"],
                    end_id=record["end_id"],
                    props=props,
                ).consume()

        copied += len(records)
        print(f"Copied relationships: {copied}")


def remove_copy_markers(target_driver) -> None:
    with target_driver.session() as session:
        session.run(f"MATCH (n) REMOVE n.{quote_name(COPY_ID_PROP)}").consume()


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy a Neo4j database.")
    parser.add_argument(
        "--clear-target",
        action="store_true",
        help="Delete all target nodes before copying.",
    )
    parser.add_argument(
        "--keep-copy-markers",
        action="store_true",
        help=f"Keep temporary {COPY_ID_PROP} properties on target nodes.",
    )
    args = parser.parse_args()

    source_uri = os.getenv("SOURCE_NEO4J_URI") or env_required("NEO4J_URI")
    source_user = os.getenv("SOURCE_NEO4J_USER") or env_required("NEO4J_USER")
    source_password = os.getenv("SOURCE_NEO4J_PASSWORD") or env_required("NEO4J_PASSWORD")

    target_uri = os.getenv("TARGET_NEO4J_URI", "bolt://localhost:7687")
    target_user = os.getenv("TARGET_NEO4J_USER", "neo4j")
    target_password = os.getenv("TARGET_NEO4J_PASSWORD", "password")

    print(f"Source: {source_uri}")
    print(f"Target: {target_uri}")

    source_driver = connect(source_uri, source_user, source_password)
    target_driver = connect(target_uri, target_user, target_password)

    try:
        source_nodes, source_rels = count_source(source_driver)
        print(f"Source contains {source_nodes} nodes and {source_rels} relationships.")

        if args.clear_target:
            print("Clearing target database...")
            clear_target(target_driver)

        copied_nodes = copy_nodes(source_driver, target_driver)
        copied_rels = copy_relationships(source_driver, target_driver)

        if not args.keep_copy_markers:
            remove_copy_markers(target_driver)

        print(f"Done. Copied {copied_nodes} nodes and {copied_rels} relationships.")
    finally:
        source_driver.close()
        target_driver.close()


if __name__ == "__main__":
    main()
