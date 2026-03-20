"""
RAG Engine for KrishiIntel AI — Portfolio Intelligence
FAISS vector store + SQLite aggregation + Groq LLM answer generation.
Falls back to full-dataset statistical analysis when API is unavailable.
"""

import json
import os
import re
import sqlite3
import threading
import requests
from typing import Dict, List, Optional, Tuple
from collections import Counter

from config import GROQ_MODEL, GROQ_API_URL, GROQ_TIMEOUT_SECONDS

# ─── Lazy imports (heavy libs loaded only when needed) ──────────────────────
_faiss = None
_SentenceTransformer = None


def _ensure_faiss():
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


def _ensure_st():
    global _SentenceTransformer
    if _SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer
        _SentenceTransformer = SentenceTransformer
    return _SentenceTransformer


# ─── Query classification keywords ──────────────────────────────────────────
AGGREGATE_KEYWORDS = [
    "average", "total", "summary", "portfolio", "trend", "all",
    "overall", "statistics", "stats", "overview", "report",
    "count", "how many", "sum", "min", "max",
]

# ─── SQL keyword routing ─────────────────────────────────────────────────────
SQL_KEYWORDS = ["average", "count", "total", "sum", "min", "max", "how many"]

# Predefined SQL queries mapped by detected intent
_SQL_TEMPLATES: Dict[str, Tuple[str, str]] = {
    "average_cost": (
        "SELECT ROUND(AVG(asset_cost), 2) AS result FROM invoices",
        "The average asset cost across all invoices is ₹{result:,.2f}.",
    ),
    "total_cost": (
        "SELECT ROUND(SUM(asset_cost), 2) AS result FROM invoices",
        "The total asset cost across all invoices is ₹{result:,.2f}.",
    ),
    "count_all": (
        "SELECT COUNT(*) AS result FROM invoices",
        "There are {result} invoices in the portfolio.",
    ),
    "max_cost": (
        "SELECT MAX(asset_cost) AS result FROM invoices",
        "The maximum asset cost in the portfolio is ₹{result:,.0f}.",
    ),
    "min_cost": (
        "SELECT MIN(asset_cost) AS result FROM invoices",
        "The minimum asset cost in the portfolio is ₹{result:,.0f}.",
    ),
    "average_hp": (
        "SELECT ROUND(AVG(horse_power), 1) AS result FROM invoices",
        "The average horse power across all invoices is {result} HP.",
    ),
    "count_by_model": (
        "SELECT model_name, COUNT(*) AS cnt FROM invoices GROUP BY model_name ORDER BY cnt DESC LIMIT 10",
        None,  # formatted dynamically
    ),
    "count_by_dealer": (
        "SELECT dealer_name, COUNT(*) AS cnt FROM invoices GROUP BY dealer_name ORDER BY cnt DESC LIMIT 10",
        None,
    ),
    "count_by_region": (
        "SELECT region, COUNT(*) AS cnt FROM invoices GROUP BY region ORDER BY cnt DESC LIMIT 10",
        None,
    ),
    "total_by_region": (
        "SELECT region, ROUND(SUM(asset_cost), 2) AS total FROM invoices GROUP BY region ORDER BY total DESC",
        None,
    ),
    "average_cost_by_model": (
        "SELECT model_name, ROUND(AVG(asset_cost), 2) AS avg_cost FROM invoices GROUP BY model_name ORDER BY avg_cost DESC LIMIT 10",
        None,
    ),
}


def _detect_sql_intent(query: str) -> Optional[str]:
    """Map a user query to a predefined SQL template key."""
    q = query.lower()

    # Count queries
    if any(w in q for w in ["how many", "count", "number of"]):
        if any(w in q for w in ["model", "tractor"]):
            return "count_by_model"
        if any(w in q for w in ["dealer", "vendor"]):
            return "count_by_dealer"
        if any(w in q for w in ["region", "state", "area"]):
            return "count_by_region"
        return "count_all"

    # Average queries
    if "average" in q or "avg" in q or "mean" in q:
        if any(w in q for w in ["hp", "horse power", "horsepower", "horse_power"]):
            return "average_hp"
        if any(w in q for w in ["model"]):
            return "average_cost_by_model"
        return "average_cost"

    # Total / Sum
    if "total" in q or "sum" in q:
        if any(w in q for w in ["region", "state"]):
            return "total_by_region"
        return "total_cost"

    # Min / Max
    if "max" in q or "highest" in q or "most expensive" in q or "largest" in q:
        return "max_cost"
    if "min" in q or "lowest" in q or "cheapest" in q or "smallest" in q:
        return "min_cost"

    return None


def _is_aggregate_query(query: str) -> bool:
    """Determine if a query needs the full dataset (aggregate) or top-K retrieval."""
    q = query.lower()
    return any(kw in q for kw in AGGREGATE_KEYWORDS)


class InvoiceKnowledgeBase:
    """FAISS + SQLite + Groq LLM knowledge base over processed invoices."""

    def __init__(self, db_path: str = "data/invoices_db.json"):
        self.db_path = db_path
        self.invoices: List[Dict] = []
        self.texts: List[str] = []
        self.index = None  # FAISS index
        self.embed_model = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        self._ready = False
        self._lock = threading.Lock()  # Thread safety for concurrent ingestion

    # ─── Initialization ──────────────────────────────────────────────────

    def initialize(self):
        """Load data, build FAISS index, and populate SQLite. Call once at startup."""
        print("🔧 Initializing RAG engine …")
        self._load_invoices()
        self._build_embeddings()
        self._build_sqlite()
        self._ready = True
        print(f"✅ RAG engine ready — {len(self.invoices)} invoices indexed")

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ─── Data loading ────────────────────────────────────────────────────

    def _load_invoices(self):
        if not os.path.exists(self.db_path):
            # Do NOT auto-process images on startup — just create an empty DB
            print(f"⚠️  Invoice DB not found at {self.db_path}")
            print("   Run `python generate_invoice_db.py` offline to populate it.")
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(self.db_path, "r", encoding="utf-8") as f:
            self.invoices = json.load(f)

        # Convert each invoice to a searchable text string
        self.texts = [self._invoice_to_text(inv) for inv in self.invoices]
        print(f"📄 Loaded {len(self.invoices)} invoices from {self.db_path}")

    @staticmethod
    def _invoice_to_text(inv: Dict) -> str:
        """Convert an invoice dict to a descriptive text for embedding."""
        parts = [
            f"Invoice {inv.get('doc_id', 'N/A')}",
            f"Dealer: {inv.get('dealer_name', 'N/A')}",
            f"Model: {inv.get('model_name', 'N/A')}",
            f"Horse Power: {inv.get('horse_power', 'N/A')} HP",
            f"Asset Cost: {inv.get('asset_cost', 'N/A')}",
        ]
        if inv.get("region"):
            parts.append(f"Region: {inv['region']}")
        if inv.get("invoice_date"):
            parts.append(f"Date: {inv['invoice_date']}")
        return ". ".join(parts)

    # ─── FAISS embeddings ────────────────────────────────────────────────

    def _build_embeddings(self):
        """Build FAISS index from invoice texts using sentence-transformers."""
        SentenceTransformer = _ensure_st()

        print("🧠 Loading sentence-transformer model …")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        self._rebuild_faiss_index()

    def _rebuild_faiss_index(self):
        """Rebuild the entire FAISS index from current self.texts.
        Requires self.embed_model to be loaded already."""
        import numpy as np
        faiss = _ensure_faiss()

        if not self.texts:
            # No texts to index — create empty index
            dim = 384  # all-MiniLM-L6-v2 output dimension
            self.index = faiss.IndexFlatIP(dim)
            print("✅ FAISS index built — 0 vectors (empty DB)")
            return

        print("📐 Encoding invoice texts …")
        embeddings = self.embed_model.encode(self.texts, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner product = cosine after normalization
        self.index.add(embeddings)
        print(f"✅ FAISS index built — {self.index.ntotal} vectors, dim={dim}")

    # ─── SQLite ──────────────────────────────────────────────────────────

    def _build_sqlite(self):
        """Populate an in-memory SQLite database with invoice records."""
        self.sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        cur = self.sqlite_conn.cursor()
        cur.execute("""
            CREATE TABLE invoices (
                doc_id TEXT PRIMARY KEY,
                dealer_name TEXT,
                model_name TEXT,
                horse_power REAL,
                asset_cost REAL,
                region TEXT,
                invoice_date TEXT,
                confidence REAL
            )
        """)
        for inv in self.invoices:
            cur.execute(
                "INSERT OR IGNORE INTO invoices VALUES (?,?,?,?,?,?,?,?)",
                (
                    inv.get("doc_id"),
                    inv.get("dealer_name"),
                    inv.get("model_name"),
                    inv.get("horse_power"),
                    inv.get("asset_cost"),
                    inv.get("region"),
                    inv.get("invoice_date"),
                    inv.get("confidence"),
                ),
            )
        self.sqlite_conn.commit()
        print(f"✅ SQLite in-memory DB populated — {len(self.invoices)} rows")

    # ─── Dynamic ingestion ───────────────────────────────────────────────

    def ingest_invoice(self, invoice: Dict) -> bool:
        """
        Incrementally add a new invoice to the RAG knowledge base.
        Updates FAISS index, SQLite DB, and persists to invoices_db.json.
        Thread-safe — can be called from concurrent API requests.
        If doc_id already exists, updates the record and rebuilds FAISS index.

        Returns True on success, False on failure.
        """
        import numpy as np

        doc_id = invoice.get("doc_id")
        if not doc_id:
            print("⚠️  Skipping ingestion: invoice has no doc_id")
            return False

        with self._lock:
            try:
                # ── 1. Guard: load embedding model if not yet loaded ──
                if self.embed_model is None:
                    SentenceTransformer = _ensure_st()
                    print("🧠 Loading sentence-transformer model …")
                    self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

                # ── 2. Guard: initialize SQLite if not yet created ──
                if self.sqlite_conn is None:
                    self._build_sqlite()

                # ── 3. Generate text and validate ──
                text = self._invoice_to_text(invoice)
                if not text or not text.strip():
                    print(f"⚠️  Skipping ingestion for '{doc_id}': empty text")
                    return False

                # ── 4. Dedup: update in-place if doc_id already exists ──
                existing_idx = None
                for i, inv in enumerate(self.invoices):
                    if inv.get("doc_id") == doc_id:
                        existing_idx = i
                        break

                if existing_idx is not None:
                    # Update existing record
                    self.invoices[existing_idx] = invoice
                    self.texts[existing_idx] = text
                    # Rebuild FAISS index (IndexFlatIP doesn't support update)
                    print("♻️  Rebuilding FAISS index after update...")
                    self._rebuild_faiss_index()
                else:
                    # New invoice — append and incrementally add to FAISS
                    self.invoices.append(invoice)
                    self.texts.append(text)

                    faiss = _ensure_faiss()
                    embedding = self.embed_model.encode([text], show_progress_bar=False)
                    embedding = np.array(embedding, dtype="float32")
                    faiss.normalize_L2(embedding)

                    if self.index is None:
                        dim = embedding.shape[1]
                        self.index = faiss.IndexFlatIP(dim)

                    self.index.add(embedding)

                # ── 5. Update SQLite (INSERT OR REPLACE for dedup) ──
                cur = self.sqlite_conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO invoices VALUES (?,?,?,?,?,?,?,?)",
                    (
                        doc_id,
                        invoice.get("dealer_name"),
                        invoice.get("model_name"),
                        invoice.get("horse_power"),
                        invoice.get("asset_cost"),
                        invoice.get("region"),
                        invoice.get("invoice_date"),
                        invoice.get("confidence"),
                    ),
                )
                self.sqlite_conn.commit()

                # ── 6. Persist to JSON file (compact, no indent) ──
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(self.invoices, f, ensure_ascii=False)

                action = "Updated" if existing_idx is not None else "Ingested"
                print(f"📥 {action} invoice '{doc_id}' in RAG — "
                      f"total: {len(self.invoices)}, FAISS: {self.index.ntotal}")
                return True

            except Exception as e:
                print(f"⚠️  RAG ingestion failed for '{doc_id}': {e}")
                return False

    # ─── Query entry point ───────────────────────────────────────────────

    def query(self, user_query: str) -> Dict:
        """
        Route a user query to SQL, full-dataset RAG, or top-K RAG path.
        Returns: { "answer": str, "sources": list[str], "query_type": str }
        """
        if not self._ready:
            return {"answer": "RAG engine is not initialized yet.", "sources": [], "query_type": "error"}

        q_lower = user_query.lower()

        # 1. Check for SQL keyword routing (exact aggregation)
        if any(kw in q_lower for kw in SQL_KEYWORDS):
            intent = _detect_sql_intent(user_query)
            if intent:
                return self._run_sql(intent)

        # 2. Classify: aggregate queries use FULL dataset, specific queries use FAISS
        if _is_aggregate_query(user_query):
            return self._aggregate_query(user_query)

        # 3. Specific queries: FAISS top-K retrieval
        return self._rag_query(user_query)

    # ─── SQL path ────────────────────────────────────────────────────────

    def _run_sql(self, intent: str) -> Dict:
        """Execute a predefined SQL query and format the answer."""
        template = _SQL_TEMPLATES.get(intent)
        if not template:
            return {"answer": "Not enough data available", "sources": [], "query_type": "sql"}

        sql, answer_fmt = template
        cur = self.sqlite_conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception as e:
            return {"answer": f"Query error: {str(e)}", "sources": [], "query_type": "error"}

        if not rows:
            return {"answer": "Not enough data available", "sources": [], "query_type": "sql"}

        # Single-value result
        if answer_fmt and len(rows) == 1 and len(rows[0]) == 1:
            result = rows[0][0]
            if result is None:
                return {"answer": "Not enough data available", "sources": [], "query_type": "sql"}
            return {
                "answer": answer_fmt.format(result=result),
                "sources": [],
                "query_type": "sql",
                "intent": intent,
            }

        # Multi-row / grouped result
        col_names = [desc[0] for desc in cur.description]
        records = [dict(zip(col_names, row)) for row in rows]
        lines = []
        for rec in records:
            vals = list(rec.values())
            if len(vals) == 2:
                label, value = vals
                if isinstance(value, float) and value > 1000:
                    lines.append(f"• {label}: ₹{value:,.0f}")
                else:
                    lines.append(f"• {label}: {value}")
        answer = "\n".join(lines) if lines else str(records)

        return {
            "answer": answer,
            "sources": [],
            "query_type": "sql",
            "intent": intent,
        }

    # ─── Aggregate RAG path (full dataset) ───────────────────────────────

    def _aggregate_query(self, user_query: str) -> Dict:
        """Use ALL invoices as context for aggregate/summary queries."""
        if not self.invoices:
            return {"answer": "No invoice data available in the portfolio.", "sources": [], "query_type": "aggregate"}

        # Build context from ALL invoices
        context_parts = []
        source_ids = []
        for inv in self.invoices:
            context_parts.append(json.dumps(inv, ensure_ascii=False))
            source_ids.append(inv.get("doc_id", "unknown"))
        context = "\n---\n".join(context_parts)

        # Call Groq LLM with full context
        answer = self._call_llm(user_query, context)

        return {
            "answer": answer,
            "sources": source_ids[:10],  # limit source list display
            "query_type": "aggregate",
            "total_invoices_analyzed": len(self.invoices),
        }

    # ─── Top-K RAG path (FAISS retrieval) ────────────────────────────────

    def _rag_query(self, user_query: str, top_k: int = 10) -> Dict:
        """Retrieve top-k invoices via FAISS and generate answer with LLM."""
        import numpy as np

        faiss = _ensure_faiss()

        if self.index is None or self.index.ntotal == 0:
            return {"answer": "No invoice data available.", "sources": [], "query_type": "rag"}

        # Clamp top_k to available invoices
        actual_k = min(top_k, self.index.ntotal)

        # Encode query
        query_vec = self.embed_model.encode([user_query])
        query_vec = np.array(query_vec, dtype="float32")
        faiss.normalize_L2(query_vec)

        # Search
        scores, indices = self.index.search(query_vec, actual_k)
        retrieved = []
        source_ids = []
        for idx in indices[0]:
            if 0 <= idx < len(self.invoices):
                retrieved.append(self.invoices[idx])
                source_ids.append(self.invoices[idx].get("doc_id", "unknown"))

        if not retrieved:
            return {"answer": "Not enough data available", "sources": [], "query_type": "rag"}

        # Build context
        context_parts = []
        for inv in retrieved:
            context_parts.append(json.dumps(inv, ensure_ascii=False))
        context = "\n---\n".join(context_parts)

        # Call LLM (Groq) with automatic fallback
        answer = self._call_llm(user_query, context)

        return {
            "answer": answer,
            "sources": source_ids,
            "query_type": "rag",
        }

    # ─── Groq LLM Integration ───────────────────────────────────────────

    def _call_llm(self, user_query: str, context: str) -> str:
        """Generate a grounded answer using Groq API (llama3-70b-8192).
        Falls back to _fallback_answer on any failure."""

        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            print("⚠️  GROQ_API_KEY not set — using fallback answer")
            return self._fallback_answer(user_query)

        prompt = f"""You are KrishiIntel AI, an agricultural invoice intelligence assistant.

Answer the user's question using ONLY the invoice data provided below.

RULES:
1. Base your answer strictly on the provided invoice data.
2. If the data does not contain enough information to answer, reply EXACTLY: "Not enough data available"
3. Do NOT make up or hallucinate any data.
4. Be concise and professional.
5. When mentioning costs, use ₹ symbol and Indian number formatting.
6. Reference specific invoice IDs when relevant.
7. Provide structured insights when answering summary/portfolio questions.

INVOICE DATA:
{context}

USER QUESTION: {user_query}"""

        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are KrishiIntel AI, an expert agricultural invoice intelligence assistant. Answer concisely using only provided data."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3,
        }

        try:
            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=GROQ_TIMEOUT_SECONDS,
            )

            if response.status_code == 429:
                print("⚠️  Groq API rate limited — using fallback")
                return self._fallback_answer(user_query)

            if response.status_code >= 500:
                print(f"⚠️  Groq API server error {response.status_code} — using fallback")
                return self._fallback_answer(user_query)

            if response.status_code >= 400:
                print(f"⚠️  Groq API client error {response.status_code}: {response.text[:200]} — using fallback")
                return self._fallback_answer(user_query)

            result = response.json()

            # OpenAI-compatible response format
            choices = result.get("choices", [])
            if choices and len(choices) > 0:
                answer = choices[0].get("message", {}).get("content", "").strip()
            else:
                answer = ""

            if not answer:
                print("⚠️  Groq API returned empty response — using fallback")
                return self._fallback_answer(user_query)

            return answer

        except requests.exceptions.Timeout:
            print("⚠️  Groq API timed out — using fallback")
            return self._fallback_answer(user_query)
        except requests.exceptions.ConnectionError:
            print("⚠️  Groq API connection error — using fallback")
            return self._fallback_answer(user_query)
        except Exception as e:
            print(f"⚠️  Groq API unexpected error: {e} — using fallback")
            return self._fallback_answer(user_query)

    # ─── Fallback: Full-dataset statistical answer ───────────────────────

    def _fallback_answer(self, user_query: str) -> str:
        """Generate a meaningful answer from the FULL dataset when Groq API is unavailable.
        Analyzes ALL invoices and computes comprehensive statistics."""
        try:
            all_invoices = self.invoices if self.invoices else []

            if not all_invoices:
                return "No invoice data is currently available in the portfolio."

            count = len(all_invoices)
            costs = [inv.get("asset_cost") for inv in all_invoices if inv.get("asset_cost") and inv.get("asset_cost") > 0]
            models = [inv.get("model_name") for inv in all_invoices if inv.get("model_name")]
            dealers = [inv.get("dealer_name") for inv in all_invoices if inv.get("dealer_name")]
            hps = [inv.get("horse_power") for inv in all_invoices if inv.get("horse_power") and inv.get("horse_power") > 0]

            parts = [f"Based on analysis of {count} invoice{'s' if count != 1 else ''} in the portfolio:\n"]

            # Cost statistics
            if costs:
                avg_cost = sum(costs) / len(costs)
                parts.append(f"📊 **Cost Overview:**")
                parts.append(f"  • Average asset cost: ₹{avg_cost:,.0f}")
                parts.append(f"  • Cost range: ₹{min(costs):,.0f} – ₹{max(costs):,.0f}")
                parts.append(f"  • Total portfolio value: ₹{sum(costs):,.0f}")

            # Horse power statistics
            if hps:
                avg_hp = sum(hps) / len(hps)
                parts.append(f"\n🔧 **Horse Power:**")
                parts.append(f"  • Average HP: {avg_hp:.1f}")
                parts.append(f"  • Range: {min(hps):.0f} – {max(hps):.0f} HP")

            # Top models
            if models:
                model_counts = Counter(models).most_common(5)
                parts.append(f"\n🚜 **Top Tractor Models:**")
                for model, cnt in model_counts:
                    parts.append(f"  • {model}: {cnt} invoice{'s' if cnt != 1 else ''}")

            # Top dealers
            if dealers:
                dealer_counts = Counter(dealers).most_common(5)
                parts.append(f"\n🏢 **Top Dealers:**")
                for dealer, cnt in dealer_counts:
                    parts.append(f"  • {dealer}: {cnt} invoice{'s' if cnt != 1 else ''}")

            # Insights
            parts.append(f"\n💡 **Insights:**")
            if costs and len(costs) >= 2:
                median_cost = sorted(costs)[len(costs) // 2]
                parts.append(f"  • Median asset cost is ₹{median_cost:,.0f}, suggesting a mid-range portfolio.")
            if models:
                parts.append(f"  • {len(set(models))} unique tractor models across {count} invoices.")

            return "\n".join(parts)

        except Exception:
            return "I analyzed the portfolio but encountered an issue generating the summary. Please try a more specific query."

    # ─── Portfolio stats ─────────────────────────────────────────────────

    def get_portfolio_stats(self) -> Dict:
        """Return summary statistics for the portfolio dashboard."""
        if not self._ready or not self.sqlite_conn:
            return {}

        cur = self.sqlite_conn.cursor()
        stats = {}

        cur.execute("SELECT COUNT(*) FROM invoices")
        stats["total_invoices"] = cur.fetchone()[0]

        cur.execute("SELECT ROUND(AVG(asset_cost), 2) FROM invoices")
        stats["avg_asset_cost"] = cur.fetchone()[0]

        cur.execute("SELECT ROUND(SUM(asset_cost), 2) FROM invoices")
        stats["total_portfolio_value"] = cur.fetchone()[0]

        cur.execute("SELECT ROUND(AVG(horse_power), 1) FROM invoices")
        stats["avg_horse_power"] = cur.fetchone()[0]

        cur.execute("SELECT MIN(asset_cost), MAX(asset_cost) FROM invoices")
        row = cur.fetchone()
        stats["min_asset_cost"] = row[0]
        stats["max_asset_cost"] = row[1]

        # Top 5 models
        cur.execute(
            "SELECT model_name, COUNT(*) AS cnt FROM invoices GROUP BY model_name ORDER BY cnt DESC LIMIT 5"
        )
        stats["top_models"] = [{"model": r[0], "count": r[1]} for r in cur.fetchall()]

        # Top 5 dealers
        cur.execute(
            "SELECT dealer_name, COUNT(*) AS cnt FROM invoices GROUP BY dealer_name ORDER BY cnt DESC LIMIT 5"
        )
        stats["top_dealers"] = [{"dealer": r[0], "count": r[1]} for r in cur.fetchall()]

        # Regional distribution
        cur.execute(
            "SELECT region, COUNT(*) AS cnt FROM invoices GROUP BY region ORDER BY cnt DESC"
        )
        stats["region_distribution"] = [{"region": r[0], "count": r[1]} for r in cur.fetchall()]

        return stats
