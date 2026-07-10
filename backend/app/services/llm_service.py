"""
LLM Service using Google Gemini 1.5 Flash (FREE tier).
- 15 requests/minute
- 1,000,000 tokens/day
- 1M context window (huge — can handle long documents)
"""
import json
import asyncio
import base64
import httpx
from typing import AsyncGenerator
from contextvars import ContextVar
import google.generativeai as genai
from app.config import settings
from app.utils.exceptions import LLMUnavailableError
from app.utils.text_utils import truncate_for_llm, estimate_token_count

# Request-scoped active LLM provider ContextVar
active_llm_provider: ContextVar[str] = ContextVar("active_llm_provider", default="gemini")


class LLMService:
    def __init__(self):
        self.gemini_available = bool(settings.GEMINI_API_KEY)
        
        if self.gemini_available:
            # Configure to use REST transport instead of gRPC to prevent connection hangs
            genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")

            # Flash model — free tier, very fast, 1M context
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_FULL,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                ),
            )

            # Separate model for streaming chat (no JSON constraint)
            self.chat_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_FAST,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )
        else:
            print("[LLMService] GEMINI_API_KEY is not set. Gemini features are disabled; falling back to local Ollama.")

    def _get_provider(self) -> str:
        """Get the active provider, falling back to ollama if Gemini is unavailable."""
        if not self.gemini_available:
            return "ollama"
        return active_llm_provider.get()

    async def is_ollama_available(self) -> bool:
        """Check if local Ollama service is running."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def _analyze_ollama(
        self,
        system_prompt: str,
        prompt: str,
        image_bytes: bytes = None
    ) -> tuple[dict, dict]:
        """Call Ollama for structured analysis."""
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": settings.OLLAMA_TEMPERATURE
            }
        }
        if image_bytes:
            payload["images"] = [base64.b64encode(image_bytes).decode("utf-8")]

        # Timeout 90s since local CPU inference can take some time
        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                response = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                response.raise_for_status()
                res_data = response.json()
                raw_text = res_data.get("response", "{}")
                
                result = self._parse_json(raw_text)
                
                # Estimate token usage
                prompt_tokens = res_data.get("prompt_eval_count", 0) or estimate_token_count(prompt)
                comp_tokens = res_data.get("eval_count", 0) or estimate_token_count(raw_text)
                
                token_usage = {
                    "prompt": prompt_tokens,
                    "completion": comp_tokens,
                    "total": prompt_tokens + comp_tokens,
                }
                return result, token_usage
            except Exception as e:
                print(f"[Ollama] generate failed: {e}")
                # If model doesn't support vision, retry without images
                if image_bytes and "images" in payload:
                    print("[Ollama] Retrying text-only generation...")
                    del payload["images"]
                    try:
                        response = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                        response.raise_for_status()
                        res_data = response.json()
                        raw_text = res_data.get("response", "{}")
                        result = self._parse_json(raw_text)
                        prompt_tokens = res_data.get("prompt_eval_count", 0) or estimate_token_count(prompt)
                        comp_tokens = res_data.get("eval_count", 0) or estimate_token_count(raw_text)
                        return result, {
                            "prompt": prompt_tokens,
                            "completion": comp_tokens,
                            "total": prompt_tokens + comp_tokens,
                        }
                    except Exception as re:
                        raise LLMUnavailableError()
                raise LLMUnavailableError()

    async def analyze(
        self,
        system_prompt: str,
        document_text: str,
        output_language: str = "en",
        image_bytes: bytes = None,
        mime_type: str = None
    ) -> tuple[dict, dict]:
        """
        Send document to Gemini or Ollama for structured JSON analysis.
        Returns (parsed_result_dict, token_usage_dict).
        """
        # Truncate if too long
        document_text = truncate_for_llm(document_text, max_chars=200_000)

        text_content = (
            f"{system_prompt}\n\n"
            f"OUTPUT LANGUAGE: {output_language}\n\n"
        )
        if document_text:
            text_content += (
                f"DOCUMENT TEXT EXTRACTED VIA OCR:\n"
                f"{'─' * 60}\n"
                f"{document_text}\n"
                f"{'─' * 60}\n\n"
            )
        text_content += "Please analyze this document/image and return the expected structured JSON."

        # Route to Ollama if configured
        provider = self._get_provider()
        if provider == "ollama":
            print("[LLMService] Routing analyze request to Ollama...")
            try:
                return await self._analyze_ollama(system_prompt, text_content, image_bytes)
            except Exception as e:
                print(f"[LLMService] Ollama failed: {e}. Falling back to Gemini Cloud...")

        # Gemini execution flow
        prompt_parts = [text_content]
        if image_bytes and mime_type:
            from PIL import Image
            import io
            try:
                img = Image.open(io.BytesIO(image_bytes))
                prompt_parts.append(img)
            except Exception as e:
                print(f"DEBUG LLM: Failed to open image for multimodal analysis: {e}")

        fallback_models = ["gemini-2.0-flash-lite", "gemini-flash-lite-latest", "gemini-1.5-flash"]
        for attempt in range(3):
            try:
                model_to_use = self.model
                if attempt > 0:
                    fallback_name = fallback_models[attempt - 1]
                    print(f"[LLMService] Switching to fallback model on attempt {attempt+1}: {fallback_name}")
                    model_to_use = genai.GenerativeModel(
                        model_name=fallback_name,
                        generation_config=genai.types.GenerationConfig(
                            temperature=settings.GEMINI_TEMPERATURE,
                            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                            response_mime_type="application/json",
                        ),
                    )

                response = await asyncio.to_thread(
                    model_to_use.generate_content,
                    prompt_parts,
                )
                raw_text = response.text or "{}"
                result = self._parse_json(raw_text)
                
                if not isinstance(result, dict) or not result:
                    raise ValueError("Empty or invalid JSON result")
                
                token_usage = {
                    "prompt": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total": getattr(response.usage_metadata, "total_token_count", 0),
                }
                return result, token_usage

            except Exception as e:
                print(f"[LLMService] Gemini error (attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    # Auto-fallback to Ollama if running
                    if await self.is_ollama_available():
                        print("[LLMService] Gemini failed permanently. Falling back to local Ollama...")
                        return await self._analyze_ollama(system_prompt, text_content, image_bytes)
                    raise LLMUnavailableError()
                wait = 3 ** attempt  # Slightly longer backoff for quota reset
                await asyncio.sleep(wait)

        raise LLMUnavailableError()

    async def classify_visually(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Use Gemini or Ollama to classify an image into a document type.
        Returns one of the known document type strings.
        """
        VALID_TYPES = [
            "medical", "legal_contract", "bill_utility", "receipt_invoice",
            "scam_message", "screenshot_ui", "disaster_rescue", "government_document", "unknown"
        ]

        # Route to Ollama if configured
        provider = self._get_provider()
        if provider == "ollama":
            print("[LLMService] Routing classify_visually to Ollama...")
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": (
                    "Classify this image into exactly ONE of these categories:\n"
                    "- disaster_rescue (floods, rising water, natural disasters, stranded people, emergency rescue, collapsed buildings, wildfires)\n"
                    "- medical (prescription, medical report, X-ray, lab test)\n"
                    "- legal_contract (contract, agreement, legal document)\n"
                    "- bill_utility (utility bill, invoice, electricity, water bill)\n"
                    "- receipt_invoice (store receipt, payment receipt)\n"
                    "- scam_message (phishing, fraud SMS screenshot)\n"
                    "- screenshot_ui (mobile app screenshot, website screenshot, error message)\n"
                    "- government_document (passport, ID card, official government form)\n"
                    "- unknown (none of the above)\n\n"
                    "Reply with ONLY the category name, nothing else."
                ),
                "images": [base64.b64encode(image_bytes).decode("utf-8")],
                "stream": False,
                "options": {"temperature": 0.1}
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                    response.raise_for_status()
                    res_data = response.json()
                    raw = (res_data.get("response", "unknown")).strip().lower().split()[0]
                    return raw if raw in VALID_TYPES else "unknown"
            except Exception as e:
                print(f"[Ollama] classify_visually failed: {e}")
                return "unknown"

        # Gemini execution flow
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))

        fallback_models = [settings.GEMINI_MODEL_FAST, "gemini-2.0-flash-lite", "gemini-flash-lite-latest", "gemini-1.5-flash"]
        for model_name in fallback_models:
            try:
                print(f"[LLMService] Attempting classify_visually with: {model_name}")
                simple_model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=30),
                )
                response = await asyncio.to_thread(
                    simple_model.generate_content,
                    [
                        "Classify this image into exactly ONE of these categories:\n"
                        "- disaster_rescue (floods, rising water, natural disasters, stranded people, emergency rescue, collapsed buildings, wildfires)\n"
                        "- medical (prescription, medical report, X-ray, lab test)\n"
                        "- legal_contract (contract, agreement, legal document)\n"
                        "- bill_utility (utility bill, invoice, electricity, water bill)\n"
                        "- receipt_invoice (store receipt, payment receipt)\n"
                        "- scam_message (phishing, fraud SMS screenshot)\n"
                        "- screenshot_ui (mobile app screenshot, website screenshot, error message)\n"
                        "- government_document (passport, ID card, official government form)\n"
                        "- unknown (none of the above)\n\n"
                        "Reply with ONLY the category name, nothing else.",
                        img,
                    ],
                )
                raw = (response.text or "unknown").strip().lower().split()[0]
                if raw in VALID_TYPES:
                    return raw
            except Exception as e:
                print(f"[LLMService] classify_visually failed with {model_name}: {e}")

        return "unknown"

    async def generate_title(self, text: str, doc_type: str, language: str = "en") -> str:
        """Generate a short human-readable title for the document."""
        prompt = (
            f"Given this {doc_type.replace('_', ' ')} document, generate a short title "
            f"(max 8 words, in {language}). Return ONLY the title text, nothing else.\n\n"
            f"Document excerpt:\n{text[:500]}"
        )

        provider = self._get_provider()
        if provider == "ollama":
            print("[LLMService] Routing generate_title to Ollama...")
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.5}
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                    response.raise_for_status()
                    title = response.json().get("response", "").strip().strip('"').strip("'")
                    return title[:100] if title else f"{doc_type.replace('_', ' ').title()} Document"
            except Exception as e:
                print(f"[Ollama] generate_title failed: {e}")
                return f"{doc_type.replace('_', ' ').title()} Document"

        # Gemini execution flow
        try:
            title_model = genai.GenerativeModel(settings.GEMINI_MODEL_FAST)
            response = await asyncio.to_thread(title_model.generate_content, prompt)
            title = (response.text or "").strip().strip('"').strip("'")
            return title[:100] if title else f"{doc_type.replace('_', ' ').title()} Document"
        except Exception:
            return f"{doc_type.replace('_', ' ').title()} Document"

    async def generate_suggestions(self, doc_type: str, summary: str, language: str = "en") -> list[str]:
        """Generate 5 suggested chat questions for the document."""
        prompt = (
            f"You are helping a user understand a {doc_type.replace('_', ' ')} document.\n"
            f"Document summary: {summary[:300]}\n\n"
            f"Generate exactly 5 natural follow-up questions a non-expert user would ask "
            f"to better understand this document. Write in {language}.\n"
            f'Return a JSON array of strings: ["question 1", "question 2", ...]'
        )

        provider = self._get_provider()
        if provider == "ollama":
            print("[LLMService] Routing generate_suggestions to Ollama...")
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.4}
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(f"{settings.OLLAMA_URL}/api/generate", json=payload)
                    response.raise_for_status()
                    questions = json.loads(response.json().get("response", "[]"))
                    if isinstance(questions, list):
                        return [str(q) for q in questions[:5]]
            except Exception as e:
                print(f"[Ollama] generate_suggestions failed: {e}")
            return [
                "Can you explain this document in simpler terms?",
                "What are the most important things I need to know?",
                "Are there any risks or warnings I should be aware of?",
                "What actions do I need to take?",
                "What deadlines or dates should I note?",
            ]

        # Gemini execution flow
        try:
            model = genai.GenerativeModel(
                settings.GEMINI_MODEL_FAST,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            questions = json.loads(response.text or "[]")
            if isinstance(questions, list):
                return [str(q) for q in questions[:5]]
        except Exception:
            pass
        return [
            "Can you explain this document in simpler terms?",
            "What are the most important things I need to know?",
            "Are there any risks or warnings I should be aware of?",
            "What actions do I need to take?",
            "What deadlines or dates should I note?",
        ]

    async def stream_chat(
        self,
        history: list[dict],
        doc_context: str,
        doc_type: str,
        analysis_summary: str,
        output_language: str = "en",
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response about the uploaded document.
        """
        system_instruction = (
            f"You are a helpful assistant explaining a {doc_type.replace('_', ' ')} document. "
            f"You have full access to the document content and its analysis.\n\n"
            f"DOCUMENT SUMMARY: {analysis_summary[:500]}\n\n"
            f"DOCUMENT CONTENT:\n{truncate_for_llm(doc_context, 50_000)}\n\n"
            f"RULES:\n"
            f"- Answer in {output_language}\n"
            f"- Be clear and use simple language\n"
            f"- Reference specific parts of the document when relevant\n"
            f"- For medical questions: add 'consult a doctor' reminder\n"
            f"- For legal questions: add 'consult a lawyer' reminder\n"
            f"- Use bullet points and bold for clarity\n"
            f"- Keep responses concise but complete"
        )

        provider = self._get_provider()
        if provider == "ollama":
            print("[LLMService] Routing stream_chat to Ollama...")
            # Format history for Ollama chat API
            ollama_messages = [{"role": "system", "content": system_instruction}]
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                ollama_messages.append({"role": role, "content": msg["content"]})

            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": ollama_messages,
                "stream": True,
                "options": {"temperature": 0.3}
            }

            try:
                # Stream directly via HTTP client
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", f"{settings.OLLAMA_URL}/api/chat", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                chunk = json.loads(line)
                                token = chunk.get("message", {}).get("content", "")
                                if token:
                                    yield token
                return
            except Exception as e:
                print(f"[Ollama] stream_chat failed: {e}. Falling back to Gemini...")

        # Gemini execution flow
        gemini_history = []
        for msg in history[:-1]:  # all but last
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        current_message = history[-1]["content"] if history else ""

        try:
            chat_session = self.chat_model.start_chat(history=gemini_history)
            if not gemini_history:
                current_message = f"{system_instruction}\n\nUser question: {current_message}"

            response = await asyncio.to_thread(
                chat_session.send_message,
                current_message,
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"\n\nSorry, I encountered an error. Please try again."

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from LLM response with multiple fallback strategies."""
        text = text.strip()
        
        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Handle both ```json and ``` cases
            if len(lines) >= 3:
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
        
        # Strategy 3: Find first complete JSON object
        import re
        # Match balanced braces - simplified approach
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx >= 0:
                    candidate = text[start_idx:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
        
        # Strategy 4: Regex fallback for simple objects
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Strategy 5: Fix common LLM JSON issues
        fixed = text.replace("'", '"')  # Single to double quotes
        fixed = re.sub(r',\s*}', '}', fixed)  # Trailing commas
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # All strategies failed - return empty dict
        return {}


# Module-level singleton
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
