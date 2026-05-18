"""Export the Neo4j Aura database configured in .env to local JSONL files."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase, READ_ACCESS


load_dotenv()

BATCH_SIZE = int(os.getenv("NEO4J_EXPORT_BATCH_SIZE", "1000"))
EXPORT_DIR = Path(os.getenv("NEO4J_EXPORT_DIR", "neo4j_export"))
MAX_RETRIES = int(os.getenv("NEO4J_EXPORT_MAX_RETRIES", "5"))


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for _ in file)


def run_batch(driver, query: str, **params):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with driver.session(default_access_mode=READ_ACCESS) as session:
                return list(session.run(query, **params))
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            wait_seconds = min(2**attempt, 30)
            print(f"Read failed; retrying in {wait_seconds}s ({attempt}/{MAX_RETRIES})...")
            time.sleep(wait_seconds)


def main() -> None:
    uri = os.getenv("SOURCE_NEO4J_URI") or env_required("NEO4J_URI")
    user = os.getenv("SOURCE_NEO4J_USER") or env_required("NEO4J_USER")
    password = os.getenv("SOURCE_NEO4J_PASSWORD") or env_required("NEO4J_PASSWORD")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    nodes_path = EXPORT_DIR / "nodes.jsonl"
    relationships_path = EXPORT_DIR / "relationships.jsonl"
    meta_path = EXPORT_DIR / "metadata.json"

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()

    try:
        with driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

        print(f"Exporting {node_count} nodes and {rel_count} relationships to {EXPORT_DIR}...")

        exported_nodes = count_lines(nodes_path)
        node_mode = "a" if 0 < exported_nodes < node_count else "w"
        if exported_nodes >= node_count:
            print(f"Nodes already exported: {exported_nodes}/{node_count}")
            node_mode = "a"
        with nodes_path.open(node_mode, encoding="utf-8") as file:
            while exported_nodes < node_count:
                batch = run_batch(
                    driver,
                    """
                    MATCH (n)
                    RETURN elementId(n) AS id,
                           labels(n) AS labels,
                           properties(n) AS properties
                    ORDER BY elementId(n)
                    SKIP $skip LIMIT $limit
                    """,
                    skip=exported_nodes,
                    limit=BATCH_SIZE,
                )

                if not batch:
                    break

                for record in batch:
                    file.write(
                        json.dumps(
                            {
                                "id": record["id"],
                                "labels": record["labels"],
                                "properties": record["properties"],
                            },
                            ensure_ascii=False,
                            default=str,
                        )
                        + "\n"
                    )

                exported_nodes += len(batch)
                print(f"Exported nodes: {exported_nodes}/{node_count}")

        exported_rels = count_lines(relationships_path)
        rel_mode = "a" if 0 < exported_rels < rel_count else "w"
        if exported_rels >= rel_count:
            print(f"Relationships already exported: {exported_rels}/{rel_count}")
            rel_mode = "a"
        with relationships_path.open(rel_mode, encoding="utf-8") as file:
            while exported_rels < rel_count:
                batch = run_batch(
                    driver,
                    """
                    MATCH (a)-[r]->(b)
                    RETURN elementId(r) AS id,
                           elementId(a) AS start_id,
                           elementId(b) AS end_id,
                           type(r) AS type,
                           properties(r) AS properties
                    ORDER BY elementId(r)
                    SKIP $skip LIMIT $limit
                    """,
                    skip=exported_rels,
                    limit=BATCH_SIZE,
                )

                if not batch:
                    break

                for record in batch:
                    file.write(
                        json.dumps(
                            {
                                "id": record["id"],
                                "start_id": record["start_id"],
                                "end_id": record["end_id"],
                                "type": record["type"],
                                "properties": record["properties"],
                            },
                            ensure_ascii=False,
                            default=str,
                        )
                        + "\n"
                    )

                exported_rels += len(batch)
                print(f"Exported relationships: {exported_rels}/{rel_count}")

        meta_path.write_text(
            json.dumps(
                {
                    "source_uri": uri,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "node_count": exported_nodes,
                    "relationship_count": exported_rels,
                    "batch_size": BATCH_SIZE,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(f"Done. Files written under {EXPORT_DIR.resolve()}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
