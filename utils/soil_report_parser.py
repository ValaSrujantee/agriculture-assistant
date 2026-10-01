"""Best-effort, conservative soil report text/OCR extraction."""
import io
import re
from typing import Any, Dict

VALUE_PATTERNS = {
    "N": r"(?:nitrogen|\bN\b)(?:\s+(?:content|value|level))?\s*[:=\-]?\s*(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z/%]+(?:\s*/\s*[a-zA-Z]+)?)?",
    "P": r"(?:phosphorus|\bP\b)(?:\s+(?:content|value|level))?\s*[:=\-]?\s*(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z/%]+(?:\s*/\s*[a-zA-Z]+)?)?",
    "K": r"(?:potassium|\bK\b)(?:\s+(?:content|value|level))?\s*[:=\-]?\s*(-?\d+(?:[.,]\d+)?)\s*([a-zA-Z/%]+(?:\s*/\s*[a-zA-Z]+)?)?",
    "ph": r"(?:soil\s*)?pH\s*[:=\-]?\s*(-?\d+(?:[.,]\d+)?)",
}
FLAGS = re.IGNORECASE


def extract_report_text(filename: str, file_bytes: bytes) -> str:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(file_bytes)).pages)
        except ImportError:
            return ""
        except Exception:
            return ""
    if suffix in {"jpg", "jpeg", "png"}:
        try:
            from PIL import Image
            import pytesseract
            return pytesseract.image_to_string(Image.open(io.BytesIO(file_bytes)))
        except Exception:
            return ""
    return ""


def parse_soil_report_text(text: str) -> Dict[str, Dict[str, Any]]:
    result = {}
    for field, pattern in VALUE_PATTERNS.items():
        matches = list(re.finditer(pattern, text or "", FLAGS))
        parsed = []
        for match in matches:
            raw = match.group(1).replace(",", ".")
            try:
                number = float(raw)
            except ValueError:
                continue
            unit = (match.group(2) or "").replace(" ", "") if field != "ph" else ""
            if field == "ph" and not 0 <= number <= 14:
                continue
            parsed.append((number, unit))
        distinct = {(value, unit.lower()) for value, unit in parsed}
        if len(distinct) == 1:
            value, unit = parsed[0]
            unit_normalized = unit.lower().replace(" ", "")
            if field in {"N", "P", "K"} and unit_normalized and unit_normalized not in {"kg/ha", "kgha-1", "kg·ha-1"}:
                result[field] = {"value": None, "unit": unit,
                                 "source": "soil_report", "status": "unit_mismatch"}
            else:
                result[field] = {"value": value, "unit": unit,
                                 "source": "soil_report", "status": "detected"}
        else:
            result[field] = {"value": None, "unit": "kg/ha" if field in {"N", "P", "K"} else "",
                             "source": "soil_report", "status": "ambiguous" if parsed else "not_detected"}
    return result


def parse_soil_report(filename: str, file_bytes: bytes) -> Dict[str, Dict[str, Any]]:
    return parse_soil_report_text(extract_report_text(filename, file_bytes))
