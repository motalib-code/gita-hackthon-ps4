from langgraph.graph import StateGraph, END
from backend.state import ChakravyuhState
from backend.vector_store import initialize_milvus
from utils.embeddings import get_embeddings_instance
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Initialize Logic Components
print("Initializing Logic Components...")
milvus_client, collection_name = initialize_milvus()
embedder = get_embeddings_instance()

# Initialize Generator Model (Flan-T5 as per original app)
device = "cpu" # Sandbox
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map=device)
generator_pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)

# --- NODES ---

def router_node(state: ChakravyuhState):
    """
    Decides the retrieval strategy.
    Simple keyword heuristic for this demo.
    """
    query = state["query"].lower()
    if "image" in query or "diagram" in query or "picture" in query:
        return {"intent": "VISUAL"}
    elif "compare" in query or "conflict" in query or "difference" in query:
        return {"intent": "COMPOSITE"}
    else:
        return {"intent": "TEXT"}

def retriever_node(state: ChakravyuhState):
    """
    Queries Milvus based on intent.
    """
    query = state["query"]
    intent = state["intent"]

    query_vec = embedder.get_text_embedding(query)

    # In a full system, we'd use different vectors (CLIP vs Dense) based on intent.
    # Here we stick to Dense for everything (using Captions for images).

    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[query_vec],
        anns_field="embedding_dense",
        search_params={"metric_type": "COSINE", "params": {"nlist": 128}},
        limit=3,
        output_fields=["content_blob", "modality", "metadata"]
    )

    docs = []
    if search_res:
        for hit in search_res[0]:
            docs.append(hit)

    return {"retrieved_docs": docs}

def grader_node(state: ChakravyuhState):
    """
    Simple check if docs are relevant.
    """
    # Placeholder: Always assume relevant if score > threshold (handled by vector db implicitly)
    # Could check for empty docs
    if not state["retrieved_docs"]:
        return {"retry_count": state.get("retry_count", 0) + 1}
    return {}

def conflict_judge_node(state: ChakravyuhState):
    """
    Analyzes retrieved docs for contradictions.
    Uses a slightly better heuristic than pure keyword matching.
    """
    docs = state["retrieved_docs"]
    if len(docs) < 2:
        return {"conflict_detected": False}

    # We compare the top 2 docs
    doc_a = docs[0]['entity']
    doc_b = docs[1]['entity']

    text_a = doc_a.get('content_blob', '').lower()
    text_b = doc_b.get('content_blob', '').lower()

    # 1. Check for antonyms in critical statuses (Simple dictionary approach)
    # Ideally this uses an NLI model, but for sandbox we stick to robust heuristics
    # to avoid downloading a 500MB+ model just for this check if not requested.

    conflict_pairs = [
        ("high", "low"),
        ("increase", "decrease"),
        ("start", "stop"),
        ("green", "red"),
        ("safe", "dangerous"),
        ("active", "inactive"),
        ("on", "off")
    ]

    conflict_detected = False
    reason = ""

    for word1, word2 in conflict_pairs:
        # If one doc contains word1 and the other contains word2
        if (word1 in text_a and word2 in text_b) or (word2 in text_a and word1 in text_b):
            # Weak check: Ensure they are talking about similar things (overlap)
            # Jaccard similarity of words
            words_a = set(text_a.split())
            words_b = set(text_b.split())
            overlap = len(words_a.intersection(words_b))

            if overlap > 3: # Arbitrary threshold for "same topic"
                conflict_detected = True
                reason = f"Conflict detected: One source mentions '{word1}' while the other mentions '{word2}' regarding similar context."
                break

    return {"conflict_detected": conflict_detected, "conflict_reasoning": reason}

def generator_node(state: ChakravyuhState):
    """
    Synthesizes the answer.
    """
    docs = state["retrieved_docs"]
    query = state["query"]

    context = "\n".join([f"Source ({d['entity']['modality']}): {d['entity']['content_blob']}" for d in docs])

    prompt = f"""
    Answer the question based on the context.
    Context: {context}
    Question: {query}
    Answer:
    """

    response = generator_pipe(prompt)[0]['generated_text']

    return {"final_answer": response}

# --- GRAPH ---

def build_graph():
    workflow = StateGraph(ChakravyuhState)

    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("judge", conflict_judge_node)
    workflow.add_node("generator", generator_node)

    workflow.set_entry_point("router")

    workflow.add_edge("router", "retriever")
    workflow.add_edge("retriever", "grader")
    workflow.add_edge("grader", "judge")
    workflow.add_edge("judge", "generator")
    workflow.add_edge("generator", END)

    return workflow.compile()

# Global App Graph
app_graph = build_graph()
