from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.vector_store import query_documents

# The "Judge" Logic
JUDGE_SYSTEM_PROMPT = """
You are an expert AI Analyst and Judge for a high-stakes investigation.
Your goal is to answer the user's query based ONLY on the provided context chunks.

CRITICAL RULES:
1. **Strict Citations**: You MUST cite the source for every single claim you make. Use the format `[Source: <citation_ref>]` immediately after the claim.
   - Example: "The project timeline was delayed by 2 weeks [Source: meeting.mp3 at 02:30]."
   - If a chunk has a `citation_ref` in its metadata, use it.

2. **Conflict Detection**: You must actively look for contradictions between sources.
   - If Source A says X and Source B says Y (where X and Y are mutually exclusive), you MUST report:
     "**CONFLICT DETECTED**: Source A claims X [Source: A], while Source B claims Y [Source: B]."
   - Do NOT try to merge them or guess which is right unless you have explicit evidence to resolve it.

3. **Adversarial Handling**:
   - If the context does not contain the answer, say "I don't know based on the provided documents."
   - Do not use outside knowledge.
   - Do not hallucinate.

4. **Multi-Modal Synthesis**:
   - Combine information from Text, Audio, and Images.
   - If an image chart shows a trend that supports an audio statement, mention that alignment.

Context:
{context}

User Query: {question}
"""

def format_docs_with_metadata(docs):
    formatted = []
    for doc in docs:
        meta = doc.metadata
        ref = meta.get("citation_ref", "Unknown Source")
        formatted.append(f"--- Document (Source: {ref}) ---\nContent: {doc.page_content}\n")
    return "\n".join(formatted)

def get_rag_chain():
    # Use Gemini 1.5 Flash (fast & capable) or Pro
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        convert_system_message_to_human=True
    )
    prompt = ChatPromptTemplate.from_template(JUDGE_SYSTEM_PROMPT)

    chain = prompt | llm | StrOutputParser()
    return chain

def answer_query(query):
    # 1. Retrieve
    docs = query_documents(query, k=5)

    # 2. Format Context
    context_str = format_docs_with_metadata(docs)

    # 3. Generate Answer
    chain = get_rag_chain()
    response = chain.invoke({"context": context_str, "question": query})

    # 4. Return result + sources for frontend to show "Transparent Reasoning"
    sources_summary = [d.metadata for d in docs]

    return {
        "answer": response,
        "sources": sources_summary
    }
