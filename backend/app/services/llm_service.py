"""
LLM Service using Google Gemini 1.5 Flash (FREE tier).
- 15 requests/minute
- 1,000,000 tokens/day
- 1M context window (huge — can handle long documents)
"""
import json
import asyncio
from typing import AsyncGenerator
import google.generativeai as genai
from app.config import settings
from app.utils.exceptions import LLMUnavailableError
from app.utils.text_utils import truncate_for_llm, estimate_token_count


class LLMService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set. Get your free key at https://aistudio.google.com/app/apikey")

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

    async def analyze(
        self,
        system_prompt: str,
        document_text: str,
        output_language: str = "en",
        image_bytes: bytes = None,
        mime_type: str = None
    ) -> tuple[dict, dict]:
        """
        Send document to Gemini for structured JSON analysis.
        Returns (parsed_result_dict, token_usage_dict).
        Supports multimodal image input if image_bytes and mime_type are provided.
        """
        # Truncate if somehow too long (Gemini 1.5 Flash: 1M context)
        document_text = truncate_for_llm(document_text, max_chars=200_000)

        prompt_parts = []
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
        prompt_parts.append(text_content)

        if image_bytes and mime_type:
            from PIL import Image
            import io
            try:
                img = Image.open(io.BytesIO(image_bytes))
                prompt_parts.append(img)
            except Exception as e:
                print(f"DEBUG LLM: Failed to open image for multimodal analysis: {e}")

        for attempt in range(3):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt_parts,
                )
                raw_text = response.text or "{}"

                # Parse JSON with robust parser
                result = self._parse_json(raw_text)
                
                # Validate result has expected structure
                if not isinstance(result, dict) or not result:
                    raise ValueError("Empty or invalid JSON result")
                
                token_usage = {
                    "prompt": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total": getattr(response.usage_metadata, "total_token_count", 0),
                }
                return result, token_usage

            except Exception as e:
                import traceback
                print(f"[LLMService] Error during content generation (attempt {attempt+1}/3): {e}")
                traceback.print_exc()
                if attempt == 2:
                    raise LLMUnavailableError()
                # Respect Gemini rate limit — wait before retry
                wait = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait)

        raise LLMUnavailableError()

    async def classify_visually(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Use Gemini Vision to classify an image into a document type.
        Returns one of the known document type strings.
        Used when OCR yields no/little text (e.g. flood photo, accident scene).
        """
        import io
        from PIL import Image

        VALID_TYPES = [
            "medical", "legal_contract", "bill_utility", "receipt_invoice",
            "scam_message", "screenshot_ui", "disaster_rescue", "government_document", "unknown"
        ]

        try:
            img = Image.open(io.BytesIO(image_bytes))
            simple_model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_FAST,
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
            return raw if raw in VALID_TYPES else "unknown"
        except Exception as e:
            print(f"[LLM] classify_visually failed: {e}")
            return "unknown"

    async def generate_title(self, text: str, doc_type: str, language: str = "en") -> str:
        """Generate a short human-readable title for the document."""
        prompt = (
            f"Given this {doc_type.replace('_', ' ')} document, generate a short title "
            f"(max 8 words, in {language}). Return ONLY the title text, nothing else.\n\n"
            f"Document excerpt:\n{text[:500]}"
        )
        try:
            # Use model without JSON constraint for title
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
        Yields text tokens as they arrive from Gemini.
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

        # Build Gemini chat history
        gemini_history = []
        for msg in history[:-1]:  # all but last (which is the current user message)
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        current_message = history[-1]["content"] if history else ""

        try:
            chat_session = self.chat_model.start_chat(history=gemini_history)
            # Add system context to first message if no history
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
