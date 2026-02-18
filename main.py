import base64
import io
import json
import os
import re
from typing import Optional

import streamlit as st
import vertexai
from PIL import Image
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "videograph-ai-5666b2db80fa.json"

MATHPIX_APP_ID = "turitoyvs_2d759a_2eca74"
MATHPIX_API_KEY = "7b8c835a195e8dab5dcd8ee677017e9c93777376128cf8f37fc3a534fb8f5d34"

VERTEX_PROJECT = "videograph-ai"
VERTEX_LOCATION = "europe-west4"
corpus_name = "projects/370739469923/locations/europe-west4/ragCorpora/4611686018427387904"
VERTEX_MODEL = "gemini-2.5-pro"
VERTEX_TOP_K = 5

vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)


def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def mathpix_ocr(image):
    import requests

    try:
        img_base64 = image_to_base64(image)
        url = "https://api.mathpix.com/v3/text"
        headers = {
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_API_KEY,
            "Content-Type": "application/json",
        }

        data = {
            "src": f"data:image/png;base64,{img_base64}",
            "formats": ["text", "latex_styled"],
            "data_options": {"include_asciimath": True, "include_latex": True},
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            latex_text = result.get("latex_styled", result.get("text", ""))
            if latex_text and latex_text.strip():
                return (True, latex_text)
            else:
                return (False, "No text detected in the image")
        else:
            return (False, f"Mathpix API error: {response.status_code} {response.text}")

    except requests.exceptions.Timeout:
        return (False, "OCR request timed out")
    except Exception as e:
        return (False, f"OCR Error: {str(e)}")


prompt = """
You are an SAT tutoring assistant. with access to SAT question-explanation pairs which is in latex format. 
Your task is to answer SAT questions by mimicking the explanation style of the SAT explanation documents.


when given a question:
1. find similar questions and study their explanation style
2. use the explanation style to answer the question accurately
3. Write the explanation strictly mimicking that style - whether or not the question exists in the database

Rules:
- If the question or a similar one exists in the database: use the retrieved explanation style
- Style mimicry is non-negotiable in both cases — always derive style from the database
- If no similar question is found: answer using your SAT tutor knowledge, but still mirror the explanation style from the most relevant documents you can find including how each answer choice is addressed
- Mirror the exact structure of explanations from the database including how each answer choice is addressed. Apply that same structure to every question, even new ones not in the database
- Never mention the database, retrieval, or that you searched anything
- Never say "based on the documents" or similar
- DONOT return answer or explanation in Latex format

OUTPUT FORMAT:
ANSWER: only return the correct option or value no explanation

EXPLANATION:
[Explanation written in the style derived from the database]

strictly return in the above format only. do not return anything else.
"""


def _parse_answer_explanation(text: str) -> tuple[str, str]:
    raw = (text or "").strip()
    if not raw:
        return "", ""

    upper = raw.upper()
    a_i = upper.find("ANSWER:")
    e_i = upper.find("EXPLANATION:")

    answer = ""
    explanation = ""
    if a_i != -1:
        if e_i != -1 and e_i > a_i:
            answer = raw[a_i + len("ANSWER:") : e_i].strip()
        else:
            answer = raw[a_i + len("ANSWER:") :].strip().splitlines()[0].strip()

    if e_i != -1:
        explanation = raw[e_i + len("EXPLANATION:") :].strip()

    if not answer:
        nums = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", raw)
        if nums:
            answer = nums[-1].replace(",", "")
        else:
            mc = re.search(r"\b([A-D])\b", raw)
            if mc:
                answer = mc.group(1)

    if not explanation:
        explanation = raw

    return answer, explanation


rag_retrieval_config = rag.RagRetrievalConfig(top_k=VERTEX_TOP_K)
rag_retrieval_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            rag_retrieval_config=rag_retrieval_config,
        )
    )
)
rag_model = GenerativeModel(model_name=VERTEX_MODEL, tools=[rag_retrieval_tool])


def _get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        if name in st.secrets:
            value = st.secrets.get(name)
            return str(value) if value is not None else default
    except Exception:
        pass
    return os.getenv(name, default)


def _ensure_session_state() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []


def _run_query(*, typed_question: str, image_bytes: bytes) -> dict:
    latex_result = None

    if image_bytes:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.format not in ["PNG", "JPG", "JPEG"]:
                return {"error": "Unsupported image format"}
            if not (MATHPIX_APP_ID and MATHPIX_API_KEY):
                return {
                    "error": "Mathpix credentials are missing (MATHPIX_APP_ID / MATHPIX_APP_KEY)."
                }
            success, latex_result = mathpix_ocr(image)
            if not success:
                return {"error": latex_result}
        except Exception as e:
            return {"error": f"Image processing error: {str(e)}"}

    typed_text = typed_question if typed_question is not None else ""

    if latex_result and typed_text:
        question = f"{latex_result}\n{typed_text}"
    elif latex_result:
        question = latex_result
    elif typed_text:
        question = typed_text
    else:
        return {"error": "Invalid request, missing required fields"}

    full_input = f"{prompt}\n\nQuestion:\n{question}".strip()
    response = rag_model.generate_content(contents=full_input)
    text = getattr(response, "text", "") or ""
    answer, explanation = _parse_answer_explanation(text)

    return {"answer": answer, "explanation": explanation, "raw": text}


def main() -> None:
    st.set_page_config(page_title="RAG Q&A", page_icon="💬", layout="wide")
    _ensure_session_state()

    st.title("Turito AI Tutor")

    if st.button("Clear chat"):
        st.session_state.history = []
        st.rerun()

    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(turn["question"])
            if turn.get("had_image"):
                st.caption("Image uploaded.")
        with st.chat_message("assistant"):
            if turn.get("answer"):
                st.markdown(f"**ANSWER:** {turn['answer']}")
            if turn.get("explanation"):
                st.markdown("**EXPLANATION:**")
                st.markdown(turn["explanation"])
            else:
                st.markdown(turn.get("raw", ""))

    st.divider()
    with st.form("ask_form", clear_on_submit=True):
        st.subheader("Ask")
        uploaded = st.file_uploader(
            "Upload an image (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        typed_question = st.text_area(
            "Type your question (optional)",
            height=120,
            placeholder="Paste/type the question here…",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if not submitted:
        return

    had_image = uploaded is not None
    image_bytes = uploaded.getvalue() if uploaded is not None else b""

    if not image_bytes and not typed_question.strip():
        st.error("Please upload an image and/or type a question.")
        return

    with st.spinner("Thinking…"):
        try:
            merged_question = typed_question.strip() or "(image only)"
            payload = _run_query(typed_question=typed_question, image_bytes=image_bytes)

            if payload.get("error"):
                st.error(payload["error"])
                raw = payload.get("raw", "")
                if raw:
                    st.code(raw)
                return

            answer = payload.get("answer", "") or ""
            explanation = payload.get("explanation", "") or ""
            raw = payload.get("raw", "") or ""

            st.session_state.history.append(
                {
                    "question": merged_question,
                    "had_image": had_image,
                    "answer": answer,
                    "explanation": explanation,
                    "raw": raw,
                }
            )
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
