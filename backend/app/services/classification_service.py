"""
Document Classification Service.
Phase A: Rule-based keyword matching (fast, free, no API call).
Phase B: Gemini classification fallback for ambiguous documents.
"""
import re
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    document_type: str
    confidence_score: float
    detected_language: str
    risk_level: str
    urgency: str
    intent: str


# Keyword patterns per document type
# Each list has (pattern, weight) tuples
PATTERNS: dict[str, list[tuple[str, float]]] = {
    "medical": [
        (r"\b(mg|mcg|tablet|capsule|dosage|prescription|rx)\b", 2.0),
        (r"\b(medicine|drug|pharmacist|pharmaceutical|antibiotic|analgesic)\b", 2.0),
        (r"\b(paracetamol|ibuprofen|amoxicillin|metformin|aspirin|cetirizine)\b", 3.0),
        (r"\b(side effect|contraindication|overdose|dose|twice daily|once daily)\b", 2.0),
        (r"\b(warning.*medicine|take.*tablet|swallow.*capsule)\b", 2.5),
    ],
    "legal_contract": [
        (r"\b(agreement|contract|covenant|party|parties)\b", 2.0),
        (r"\b(clause|whereas|hereby|herein|hereinafter|thereof)\b", 2.5),
        (r"\b(indemnify|warrant|represent|arbitration|jurisdiction)\b", 3.0),
        (r"\b(termination|breach|penalty|liquidated damages|force majeure)\b", 2.5),
        (r"\b(non-disclosure|nda|confidential|intellectual property|proprietary)\b", 2.0),
    ],
    "bill_utility": [
        (r"\b(electricity|kilowatt|kwh|unit consumed|meter reading)\b", 3.0),
        (r"\b(water bill|gas bill|utility bill|service charge)\b", 3.0),
        (r"\b(billing period|account number|due date|arrears|connection)\b", 2.0),
        (r"\b(tariff|consumption|supply|provider|subscriber)\b", 1.5),
    ],
    "bill_bank": [
        (r"\b(bank statement|account statement|transaction history)\b", 3.0),
        (r"\b(debit|credit|balance|withdrawal|deposit|transfer)\b", 2.0),
        (r"\b(iban|swift|sort code|routing number|account holder)\b", 3.0),
        (r"\b(opening balance|closing balance|available balance|interest)\b", 2.5),
    ],
    "government": [
        (r"\b(notice|order|ordinance|gazette|tribunal|authority)\b", 2.0),
        (r"\b(pursuant to|in accordance with|regulation|compliance|mandatory)\b", 2.5),
        (r"\b(department|ministry|commissioner|respondent|appellant)\b", 2.5),
        (r"\b(penalty|fine|summons|hearing|proceeding|enforcement)\b", 2.0),
        (r"\b(tax authority|revenue|assessment|demand|income tax)\b", 2.5),
    ],
    "receipt_invoice": [
        (r"\b(receipt|invoice|bill no|order id|transaction id)\b", 3.0),
        (r"\b(subtotal|total|amount due|payment received|paid)\b", 2.0),
        (r"\b(merchant|cashier|store|shop|restaurant)\b", 1.5),
        (r"\b(item|qty|quantity|unit price|vat|gst|tax)\b", 2.0),
        (r"\b(thank you for your purchase|please keep|retain for records)\b", 2.5),
    ],
    "scam_message": [
        (r"\b(congratulations|you.?ve won|selected winner|prize|lottery)\b", 3.0),
        (r"\b(click here|verify now|confirm account|urgent action required)\b", 2.5),
        (r"\b(wire transfer|western union|gift card|cryptocurrency|bitcoin)\b", 3.0),
        (r"\b(otp|one.?time password|bank details|enter your password)\b", 2.5),
        (r"\b(account suspended|verify identity|unusual activity)\b", 2.5),
        (r"\b(limited time|expires in|act now|claim your|don.?t miss)\b", 1.5),
    ],
    "screenshot_ui": [
        (r"\b(tap to|click to|swipe|scroll|loading|error|notification)\b", 1.5),
        (r"\b(app|ios|android|settings|menu|button|dialog|popup)\b", 1.5),
        (r"\b(wifi|battery|signal|home screen|lock screen)\b", 2.0),
    ],
    "disaster_rescue": [
        (r"\b(flood|water level|rescue|stranded|evacuate|evacuation)\b", 3.0),
        (r"\b(deluge|submerged|boat rescue|heli-rescue|disaster|emergency response)\b", 3.0),
        (r"\b(rising waters|isolated persons|blocked roads|s.o.s.|sos)\b", 2.5),
        (r"\b(dispatch|first responders|civil defense|ndrf|fema)\b", 2.0),
    ],
}


class ClassificationService:

    def classify(self, text: str, filename: str = "") -> ClassificationResult:
        """Main classification — rule-based with confidence scoring."""
        lower_text = text.lower()

        # Score each document type
        scores: dict[str, float] = {}
        for doc_type, patterns in PATTERNS.items():
            score = 0.0
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, lower_text, re.IGNORECASE))
                score += matches * weight
            scores[doc_type] = score

        # Find top type
        top_type = max(scores, key=scores.get)
        top_score = scores[top_type]

        # Normalize confidence (cap at 0.97)
        total_possible = sum(len(p) * 2.0 for p in PATTERNS[top_type])
        confidence = min(top_score / max(total_possible * 0.3, 1.0), 0.97)

        # Fallback to unknown if score is too low
        if top_score < 2.0:
            top_type = "unknown"
            confidence = 0.4

        language = self._detect_language(text)
        risk_level = self._assess_risk(top_type, lower_text)
        urgency = self._assess_urgency(lower_text)
        intent = self._assess_intent(top_type)

        return ClassificationResult(
            document_type=top_type,
            confidence_score=round(confidence, 3),
            detected_language=language,
            risk_level=risk_level,
            urgency=urgency,
            intent=intent,
        )

    def _detect_language(self, text: str) -> str:
        """Detect document language using langdetect."""
        try:
            from langdetect import detect, LangDetectException
            # Use first 1000 chars for speed
            return detect(text[:1000])
        except Exception:
            return "en"

    def _assess_risk(self, doc_type: str, text_lower: str) -> str:
        """Heuristic risk level based on document type and keywords."""
        if doc_type == "scam_message":
            return "high"
        if doc_type == "legal_contract":
            danger_kw = ["penalty", "terminate", "liable", "damages", "indemnify", "unlimited liability"]
            count = sum(1 for kw in danger_kw if kw in text_lower)
            return "high" if count >= 3 else "medium" if count >= 1 else "low"
        if doc_type == "government":
            return "medium" if re.search(r"\b(penalty|fine|demand|notice)\b", text_lower) else "low"
        if doc_type == "medical":
            return "medium" if re.search(r"\b(warning|do not|contraindicated|emergency)\b", text_lower) else "low"
        if doc_type in ("bill_utility", "bill_bank", "receipt_invoice"):
            return "low"
        return "informational"

    def _assess_urgency(self, text_lower: str) -> str:
        """Extract urgency from text."""
        if re.search(r"\b(immediately|urgent|today|within 24 hours|asap|emergency)\b", text_lower):
            return "immediate"
        if re.search(r"\b(within 3 days|within 48 hours|this week|by friday)\b", text_lower):
            return "within_24h"
        if re.search(r"\b(this month|within 30 days|next week)\b", text_lower):
            return "within_week"
        return "no_urgency"

    def _assess_intent(self, doc_type: str) -> str:
        intents = {
            "medical": "understand medication",
            "legal_contract": "review contract terms",
            "bill_utility": "understand charges",
            "bill_bank": "review transactions",
            "government": "comply with requirements",
            "receipt_invoice": "track spending",
            "scam_message": "verify authenticity",
            "screenshot_ui": "understand interface",
            "unknown": "understand document",
        }
        return intents.get(doc_type, "understand document")
