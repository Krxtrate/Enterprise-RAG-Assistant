from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer
from typing import Optional
from io import BytesIO
from typing import List
from huggingface_hub import login

import chromadb
import requests
import base64
import os
import json
import random

load_dotenv()

hf_token = os.getenv("hftoken")

if hf_token:
    login(token=hf_token)

# =====================================================
# APP SETUP
# =====================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# CHROMADB + EMBEDDINGS
# =====================================================

print("Loading embedding model...")

embedder = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="company_knowledge"
)

# =====================================================
# SMALLTALK DATA
# =====================================================

smalltalk_intents = []

for filename in os.listdir("smalltalk"):

    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(
        "smalltalk",
        filename
    )

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as f:

        try:

            data = json.load(f)

            smalltalk_intents.append(
                data
            )

            print(
                f"Loaded: {filename}"
            )

        except Exception as e:

            print(
                f"Failed loading {filename}"
            )

            print(e)

print(
    f"\nLoaded {len(smalltalk_intents)} smalltalk files."
)

# =====================================================
# IMAGE GENERATION CLIENT
# =====================================================

hf_client = InferenceClient(
    api_key=hf_token
)

# =====================================================
# MODELS
# =====================================================

class Message(BaseModel):
    role: str
    content: Optional[str] = ""


class ChatRequest(BaseModel):
    messages: List[Message]


class ImageRequest(BaseModel):
    prompt: str

# =====================================================
# ROUTES
# =====================================================

@app.get("/")
def home():
    return {
        "message": "AI Assistant Running"
    }

# =====================================================
# CHAT
# =====================================================

@app.post("/generate")
def generate(chat: ChatRequest):

    conversation = ""

    if not chat.messages:
        return {
            "output": "No message received."
        }

    latest_question = ""

    for msg in reversed(chat.messages):

        if msg.role == "user":

            latest_question = (
                msg.content or ""
            )

            break

    user_text = latest_question.lower().strip()

    print(f"SMALLTALK CHECKING: '{user_text}'")

    for intent in smalltalk_intents:

        for example in intent["body"]["user_says"]:

            if (
                example["active"]
                and example["text"].lower()
                == user_text
            ):

                responses = (
                    intent["body"]
                    ["bot_says"]
                    ["en"]
                    ["en"]
                )

                print(
                    f"SMALLTALK MATCH: {user_text}"
                )

                return {
                    "output": random.choice(
                        responses
                    )["text"]
                }

    company_keywords = [
        "ABC ",
        "company",
        "service",
        "services",
        "product",
        "products",
        "contact",
        "support",
        "career",
        "careers",
        "internship",
        "employee",
        "office",
        "address",
        "email",
        "phone",
        "opsis",
        "bidcounty",
        "gam360",
        "isearch",
        "genwin",
        "seetv"
    ]

    is_company_question = any(
        keyword in latest_question.lower()
        for keyword in company_keywords
    )

    # -----------------------------------
    # VECTOR SEARCH
    # -----------------------------------

    company_context = ""

    if is_company_question:

        query_embedding = embedder.encode(
            latest_question
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=4
        )

        best_distance = results["distances"][0][0]

        print(f"\nBest Distance: {best_distance}")
        print("\nDISTANCES:")
        print(results["distances"])
        print("\nSOURCES:")
        print("\nRETRIEVED SOURCES:")

        for metadata in results["metadatas"][0]:
            print(metadata)

        retrieved_docs = []

        if best_distance < 1.4:

            distances = results["distances"][0]

            for i, distance in enumerate(distances):

                if distance < 1.4:

                    source = results["metadatas"][0][i]["source"]

                    retrieved_docs.append(
                        f"SOURCE: {source}\n\n"
                        f"{results['documents'][0][i]}"
                    )

        company_context = "\n\n".join(
                retrieved_docs
        )[:2500]

        if not retrieved_docs:
            company_context = "NO_RELEVANT_COMPANY_INFORMATION"
    
    
    else:
        company_context = ""

    print("\n==============================")
    print("USER QUESTION:")
    print(latest_question)

    if is_company_question:

        print("\nRETRIEVED DOCUMENTS:")

        for doc in results["documents"][0]:

            print("-------------------")

            print(doc[:300])

    print("==============================\n")

    # -----------------------------------
    # SYSTEM PROMPT
    # -----------------------------------

    conversation += f"""

    SYSTEM INSTRUCTION:

    You are the official AI assistant of ABC.

    COMPANY INFORMATION:

    {company_context}

    RULES:

    1. If the user asks about ABC, use COMPANY INFORMATION as the primary source.

    2. When answering questions about ABC, speak from the company's perspective.

        Use:
        - we
        - our
        - us

        instead of:
        - they
        - their
        - them

        Examples:

        Correct:
        "We offer AI-driven programmatic advertising solutions."

        Correct:
        "Our corporate office is located in Gurugram."

        Incorrect:
        "They offer AI-driven programmatic advertising solutions."

        Incorrect:
        "Their office is located in Gurugram."

    3. If the answer is present in COMPANY INFORMATION, answer using that information.

    4. If the user asks about ABC and the information is not present in the provided company information,
        respond:

        "Sorry, I couldn't find that information."

        Do not guess.
        Do not invent.
        Do not infer.

    5. If the user asks a general question unrelated to ABC, answer normally as a helpful, intelligent AI assistant.

    6. You may:
        - Explain concepts
        - Answer technical questions
        - Help with coding
        - Tell jokes
        - Engage in conversation
        - Assist with learning

    7. Never invent company-specific information.

    8. When company information is provided, use only the information explicitly present.

        Never create templates.

        Never generate:
        - [insert phone number]
        - [insert email]
        - [insert website]
        - placeholders
        - example values

        If a value is unavailable,
        omit it entirely.

    9. Answer completely and do not omit items from lists.

    10. If company information is available, answer naturally.

        Never mention:
        - COMPANY KNOWLEDGE
        - knowledge base
        - retrieved documents
        - context
        - database

        Present company information as normal factual information.

        If information is unavailable, respond only:

        "Sorry, I couldn't find that information."

        Do not explain why.
        Do not mention missing context.

    11. Never list information that is unavailable.
        
        If a field is unknown, omit it entirely.

        Do not say:
        - Not specified
        - Not available
        - Not found
        - Missing

        Simply exclude unavailable information from the answer.

    12. If COMPANY INFORMATION contains:

        NO_RELEVANT_COMPANY_INFORMATION

        and the question is about ABC,

        respond:

        "Sorry, I couldn't find that information."

    13. When answering broad questions such as:

        - Complete overview
        - Tell me about the company
        - Summarize the company

        Provide a concise summary rather than repeating every detail.

        Prioritize:

        1. Company description
        2. Services
        3. Products
        4. Technologies
        5. Policies
        6. Contact information

        Keep summaries under 300 words.

    14. If contact information is requested, only provide information explicitly present in the company information.

        Never invent phone numbers,
        websites,
        or missing contact details.

    
    """

    # -----------------------------------
    # CHAT MEMORY
    # -----------------------------------

    for msg in chat.messages[-10:]:

        if msg.role == "user":

            conversation += (
                f"<|user|>\n"
                f"{msg.content}\n"
            )

        else:

            conversation += (
                f"<|assistant|>\n"
                f"{msg.content}\n"
            )

    conversation += "<|assistant|>\n"

    print("\n===== CONTEXT SENT TO LLAMA =====")
    print(company_context[:2000])
    print("================================\n")

    # -----------------------------------
    # OLLAMA
    # -----------------------------------

    payload = {
        "model": "llama3.1:8b",
        "prompt": conversation,
        "stream": False,
        "options": {
            "num_predict": 400,
            "temperature": 0.2
        }
    }

    try:
        
        print("Sending request to Ollama...")

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )

        result = response.json()

        print(response.status_code)
        print(
            result.get("response", "")[:300]
        )

        if response.status_code != 200:
            return {
                "output": "The AI service is currently unavailable."
            }

    except requests.exceptions.RequestException:
        return {
            "output": "The AI service is currently unavailable."
        }

    return {
        "output": result.get(
            "response",
            "No response generated."
        )
    }

# =====================================================
# IMAGE GENERATION
# =====================================================

@app.post("/generate-image")
def generate_image(data: ImageRequest):

    try:
        image = hf_client.text_to_image(
            data.prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

    except Exception:
        return {
            "image": None,
            "error": "Image generation failed."
        }

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    image_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return {
        "image": image_base64
    }