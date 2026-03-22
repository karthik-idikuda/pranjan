"""PRAJNA — PhyRAG: Physics-grounded Retrieval Augmented Generation.

Novel Algorithm #4: Uses NVIDIA API (Kimi-K2.5) + ChromaDB for
physics-constrained explanations of spacecraft anomalies.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PhyRAG:
    """Physics-grounded RAG for explainable anomaly reports.

    Pipeline:
      1. Retrieve relevant documents from vector store (ChromaDB)
      2. Build physics-constrained prompt with telemetry context
      3. Generate explanation via NVIDIA API (Kimi-K2.5)
      4. Validate output against physics constraints
    """

    PHYSICS_CONSTRAINTS = {
        "temperature": {"min": -270, "max": 2000, "unit": "°C"},
        "voltage": {"min": 0, "max": 200, "unit": "V"},
        "current": {"min": 0, "max": 100, "unit": "A"},
        "pressure": {"min": 0, "max": 500, "unit": "bar"},
    }

    SYSTEM_PROMPT = """You are PRAJNA, an AI spacecraft health expert. You analyze real telemetry anomalies
detected in satellite subsystems. Your analysis must be:
1. FACTUAL — cite specific sensor values and thresholds
2. PHYSICS-GROUNDED — reference material properties, thermal limits, electrical ratings
3. ACTIONABLE — provide specific contingency recommendations
4. CONCISE — operators need quick, clear information

Format your response as:
## Anomaly Summary
<one-line summary>

## Root Cause Analysis
<physics-grounded explanation>

## Evidence
- <specific telemetry values>

## Recommended Actions
1. <immediate action>
2. <follow-up action>

## Risk Level
<WATCH | WARNING | CRITICAL>
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "moonshotai/kimi-k2.5",
        base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions",
        knowledge_base_dir: str = "data/knowledge_base",
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.model = model
        self.base_url = base_url
        self.kb_dir = Path(knowledge_base_dir)
        self._vector_store = None

    def _init_vector_store(self):
        """Initialize ChromaDB vector store with aerospace knowledge."""
        try:
            import chromadb
            self._vector_store = chromadb.Client()
            self._collection = self._vector_store.get_or_create_collection(
                name="prajna_knowledge",
                metadata={"description": "Aerospace datasheets and standards"},
            )

            # Load knowledge base documents
            if self.kb_dir.exists():
                for doc_file in self.kb_dir.glob("*.txt"):
                    content = doc_file.read_text()
                    chunks = [content[i:i+512] for i in range(0, len(content), 400)]
                    for j, chunk in enumerate(chunks):
                        self._collection.add(
                            documents=[chunk],
                            ids=[f"{doc_file.stem}_{j}"],
                            metadatas=[{"source": doc_file.name}],
                        )

                count = self._collection.count()
                logger.info(f"PhyRAG knowledge base loaded: {count} chunks")
            else:
                logger.info("No knowledge base directory found. PhyRAG will use LLM-only mode.")

        except ImportError:
            logger.warning("ChromaDB not installed. PhyRAG running without RAG.")

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve relevant documents from knowledge base.

        Args:
            query: Search query (anomaly description)
            top_k: Number of documents to retrieve

        Returns:
            List of relevant document chunks
        """
        if self._vector_store is None:
            self._init_vector_store()

        if self._collection is None or self._collection.count() == 0:
            return []

        results = self._collection.query(query_texts=[query], n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    def generate_explanation(
        self,
        anomaly_context: dict,
        node_name: str = "Unknown",
        scores: dict | None = None,
    ) -> dict:
        """Generate a physics-grounded explanation for a detected anomaly.

        Args:
            anomaly_context: dict with telemetry values, scores, predictions
            node_name: Name of the affected subsystem
            scores: SDWAP/local scores

        Returns:
            dict with 'explanation', 'risk_level', 'actions', 'sources'
        """
        # Build context string
        context_str = f"Subsystem: {node_name}\n"
        if scores:
            context_str += f"Anomaly score: {scores.get('combined', 'N/A')}\n"
            context_str += f"SDWAP propagated: {scores.get('propagated', 'N/A')}\n"

        if anomaly_context.get("telemetry_values"):
            context_str += f"Telemetry: {anomaly_context['telemetry_values']}\n"

        # Retrieve relevant docs
        query = f"spacecraft {node_name} anomaly failure mode"
        retrieved_docs = self.retrieve(query)
        docs_context = "\n---\n".join(retrieved_docs[:3]) if retrieved_docs else "No reference documents available."

        # Build prompt
        user_prompt = f"""Analyze this spacecraft anomaly:

{context_str}

Reference Documents:
{docs_context}

Provide your analysis following the required format."""

        # Call NVIDIA API
        if not self.api_key:
            return {
                "explanation": f"[PhyRAG] Anomaly detected in {node_name}. API key not configured.",
                "risk_level": "UNKNOWN",
                "actions": ["Configure NVIDIA API key"],
                "sources": [],
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 2048,
                "temperature": 0.3,
            }

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            explanation = result["choices"][0]["message"]["content"]

            # Parse risk level
            risk_level = "WATCH"
            if "CRITICAL" in explanation.upper():
                risk_level = "CRITICAL"
            elif "WARNING" in explanation.upper():
                risk_level = "WARNING"

            # Validate against physics constraints
            validated = self._validate_physics(explanation)

            return {
                "explanation": explanation,
                "risk_level": risk_level,
                "actions": self._extract_actions(explanation),
                "sources": [d[:100] for d in retrieved_docs[:3]],
                "physics_valid": validated,
            }

        except Exception as e:
            logger.error(f"PhyRAG generation failed: {e}")
            return {
                "explanation": f"[PhyRAG Error] Could not generate explanation: {str(e)}",
                "risk_level": "UNKNOWN",
                "actions": [],
                "sources": [],
            }

    def _validate_physics(self, text: str) -> bool:
        """Basic physics constraint validation on generated text."""
        # Check for obviously wrong numbers
        import re
        numbers = re.findall(r'(-?\d+\.?\d*)\s*°C', text)
        for n in numbers:
            temp = float(n)
            if temp < -273 or temp > 3000:
                logger.warning(f"PhyRAG: Physics violation — temperature {temp}°C")
                return False
        return True

    def _extract_actions(self, text: str) -> list[str]:
        """Extract recommended actions from generated text."""
        actions = []
        in_actions = False
        for line in text.split("\n"):
            if "recommended actions" in line.lower():
                in_actions = True
                continue
            if in_actions and line.strip().startswith(("1.", "2.", "3.", "4.", "-")):
                actions.append(line.strip().lstrip("0123456789.-) "))
            elif in_actions and line.startswith("#"):
                break
        return actions
