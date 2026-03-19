"""
RAG Engine for KrishiIntel AI — Portfolio Intelligence
FAISS vector store + SQLite aggregation + Gemini LLM answer generation.
"""

import json
import os
import re
import sqlite3
from typing import Dict, List, Optional, Tuple

# ─── Lazy imports (heavy libs loaded only when needed) ──────────────────────
_faiss = None
_SentenceTransformer = None
_genai = None


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


def _ensure_genai():
    global _genai
    if _genai is None:
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set. Export it before starting the server.")
        genai.configure(api_key=api_key)
        _genai = genai
    return _genai


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


class InvoiceKnowledgeBase:
    """FAISS + SQLite + Gemini knowledge base over processed invoices."""

    def __init__(self, db_path: str = "data/invoices_db.json"):
        self.db_path = db_path
        self.invoices: List[Dict] = []
        self.texts: List[str] = []
        self.index = None  # FAISS index
        self.embed_model = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        self._ready = False

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
            # Try to generate seed data
            from generate_invoice_db import ensure_invoice_db
            ensure_invoice_db(self.db_path)

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
        faiss = _ensure_faiss()
        SentenceTransformer = _ensure_st()

        print("🧠 Loading sentence-transformer model …")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        print("📐 Encoding invoice texts …")
        import numpy as np
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
        self.sqlite_conn = sqlite3.connect(":memory:")
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

    # ─── Query entry point ───────────────────────────────────────────────

    def query(self, user_query: str) -> Dict:
        """
        Route a user query to SQL or RAG path.
        Returns: { "answer": str, "sources": list[str] }
        """
        if not self._ready:
            return {"answer": "RAG engine is not initialized yet.", "sources": []}

        q_lower = user_query.lower()

        # Check for SQL keyword routing
        if any(kw in q_lower for kw in SQL_KEYWORDS):
            intent = _detect_sql_intent(user_query)
            if intent:
                return self._run_sql(intent)

        # Fallback to vector retrieval + Gemini
        return self._rag_query(user_query)

    # ─── SQL path ────────────────────────────────────────────────────────

    def _run_sql(self, intent: str) -> Dict:
        """Execute a predefined SQL query and format the answer."""
        template = _SQL_TEMPLATES.get(intent)
        if not template:
            return {"answer": "Not enough data available", "sources": []}

        sql, answer_fmt = template
        cur = self.sqlite_conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception as e:
            return {"answer": f"Query error: {str(e)}", "sources": []}

        if not rows:
            return {"answer": "Not enough data available", "sources": []}

        # Single-value result
        if answer_fmt and len(rows) == 1 and len(rows[0]) == 1:
            result = rows[0][0]
            if result is None:
                return {"answer": "Not enough data available", "sources": []}
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

    # ─── RAG path ────────────────────────────────────────────────────────

    def _rag_query(self, user_query: str, top_k: int = 7) -> Dict:
        """Retrieve top-k invoices via FAISS and generate answer with Gemini."""
        import numpy as np

        faiss = _ensure_faiss()

        # Encode query
        query_vec = self.embed_model.encode([user_query])
        query_vec = np.array(query_vec, dtype="float32")
        faiss.normalize_L2(query_vec)

        # Search
        scores, indices = self.index.search(query_vec, top_k)
        retrieved = []
        source_ids = []
        for idx in indices[0]:
            if 0 <= idx < len(self.invoices):
                retrieved.append(self.invoices[idx])
                source_ids.append(self.invoices[idx].get("doc_id", "unknown"))

        if not retrieved:
            return {"answer": "Not enough data available", "sources": []}

        # Build context
        context_parts = []
        for inv in retrieved:
            context_parts.append(json.dumps(inv, ensure_ascii=False))
        context = "\n---\n".join(context_parts)

        # Call Gemini
        answer = self._call_gemini(user_query, context)

        return {
            "answer": answer,
            "sources": source_ids,
            "query_type": "rag",
        }

    def _call_gemini(self, user_query: str, context: str) -> str:
        """Generate a grounded answer using Gemini."""
        genai = _ensure_genai()

        prompt = f"""You are KrishiIntel AI, an agricultural invoice intelligence assistant.

Answer the user's question using ONLY the invoice data provided below.

RULES:
1. Base your answer strictly on the provided invoice data.
2. If the data does not contain enough information to answer, reply EXACTLY: "Not enough data available"
3. Do NOT make up or hallucinate any data.
4. Be concise and professional.
5. When mentioning costs, use ₹ symbol and Indian number formatting.
6. Reference specific invoice IDs when relevant.

INVOICE DATA:
{context}

USER QUESTION: {user_query}

ANSWER:"""

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            answer = response.text.strip()
            if not answer:
                return "Not enough data available"
            return answer
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return f"Error generating answer: {str(e)}"

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
