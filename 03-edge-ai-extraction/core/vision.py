import math
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, List

class DocumentProcessor:
    def __init__(self):
        # In a full production setup, LayoutLMv3 is loaded here:
        # from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
        # self.processor = LayoutLMv3Processor.from_pretrained("nielsr/layoutlmv3-finetuned-funsd")
        # self.model = LayoutLMv3ForTokenClassification.from_pretrained("nielsr/layoutlmv3-finetuned-funsd")
        pass
        
    def _calculate_distance(self, box1: List[int], box2: List[int]) -> float:
        """Module A: Spatial distance calculation between bounding box centers."""
        x1_center = (box1[0] + box1[2]) / 2
        y1_center = (box1[1] + box1[3]) / 2
        x2_center = (box2[0] + box2[2]) / 2
        y2_center = (box2[1] + box2[3]) / 2
        return math.sqrt((x1_center - x2_center)**2 + (y1_center - y2_center)**2)

    def process_document(self, image: Image.Image) -> Tuple[Dict, Image.Image, bool]:
        """
        Processes a document through Module A (Extraction), Module B (Redaction), 
        and Module C (Human-in-the-loop).
        """
        # Simulated extraction data representing a LayoutLMv3 forward pass on FUNSD
        # Real flow: encoding = self.processor(image) -> outputs = self.model(**encoding)
        extracted_data = [
            {"text": "Full Name:", "label": "QUESTION", "box": [50, 50, 180, 80], "confidence": 0.99},
            {"text": "Jane Doe", "label": "ANSWER", "box": [190, 50, 350, 80], "confidence": 0.96},
            {"text": "Social Security Number:", "label": "QUESTION", "box": [50, 100, 250, 130], "confidence": 0.98},
            {"text": "***-**-1234", "label": "ANSWER", "box": [260, 100, 400, 130], "confidence": 0.81}, # Low confidence
            {"text": "Date of Birth:", "label": "QUESTION", "box": [50, 150, 180, 180], "confidence": 0.97},
            {"text": "01/01/1990", "label": "ANSWER", "box": [190, 150, 320, 180], "confidence": 0.94},
        ]
        
        # --- MODULE A: Intelligent Extraction Engine (Spatial Linking) ---
        linked_data = []
        questions = [d for d in extracted_data if d["label"] == "QUESTION"]
        answers = [d for d in extracted_data if d["label"] == "ANSWER"]
        
        for q in questions:
            best_a = None
            min_dist = float('inf')
            for a in answers:
                dist = self._calculate_distance(q["box"], a["box"])
                if dist < min_dist:
                    min_dist = dist
                    best_a = a
            if best_a:
                linked_data.append({
                    "question": q["text"], 
                    "answer": best_a["text"], 
                    "confidence": best_a["confidence"],
                    "box": best_a["box"]
                })
                
        # --- MODULE B & C: Privacy Layer & Gateway ---
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        requires_review = False
        sanitized_fields = []
        
        for field in linked_data:
            # Module C: Human-in-the-loop Confidence Gateway
            if field["confidence"] < 0.85:
                requires_review = True
                
            # Module B: Privacy & Redaction Layer (Masking ANSWER boxes)
            x1, y1, x2, y2 = field["box"]
            # Apply solid black mask
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), (0, 0, 0), -1)
            
            # Sanitization: Delete original text from OCR metadata
            sanitized_fields.append({
                "field_name": field["question"],
                "value": "[REDACTED]",
                "confidence_score": field["confidence"],
                "status": "FLAGGED_FOR_REVIEW" if field["confidence"] < 0.85 else "PROCESSED"
            })
            
        sanitized_json = {
            "document_status": "MANUAL_REVIEW_REQUIRED" if requires_review else "CLEARED",
            "extracted_fields": sanitized_fields
        }
        
        redacted_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        return sanitized_json, redacted_image, requires_review

processor_engine = DocumentProcessor()
