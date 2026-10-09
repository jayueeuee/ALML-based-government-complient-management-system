import pickle
import os
import numpy as np
from PIL import Image

class AIEngine:
    def __init__(self):
        self.cat_model = None
        self.pri_model = None
        self.vqa_pipeline = None
        self.load_nlp_models()
        self.load_cv_model()

        # Questions to ask the VQA model for each complaint category.
        # We ask multiple questions per category to improve accuracy.
        self.category_questions = {
            'Road/Pothole': [
                "Is there a pothole in this image?",
                "Is there a damaged road in this image?",
                "Is there a broken road surface in this image?",
                "Is this image of a road or street?",
            ],
            'Water Supply': [
                "Is there a water pipe in this image?",
                "Is there a water leakage in this image?",
                "Is there a broken water pipeline in this image?",
                "Is there a water tank or tap in this image?",
            ],
            'Garbage/Sanitation': [
                "Is there garbage in this image?",
                "Is there a trash dump in this image?",
                "Is there waste or litter in this image?",
                "Is there an overflowing dustbin in this image?",
            ],
            'Street Lights': [
                "Is there a street light in this image?",
                "Is there a lamp post in this image?",
                "Is there a broken light in this image?",
                "Is there an electric pole in this image?",
            ],
            'Drainage': [
                "Is there a drainage problem in this image?",
                "Is there an open manhole in this image?",
                "Is there sewage overflow in this image?",
                "Is there a blocked drain in this image?",
            ],
            'Human Security': [
                "Is there a person in this image?",
                "Is there a crowd in this image?",
                "Is there a fight or violence in this image?",
                "Is there an emergency situation in this image?",
            ],
        }

        # General descriptive questions to build image analysis summary
        self.description_questions = [
            "What is shown in this image?",
            "What is the main object in this image?",
            "What is the condition of the area in this image?",
        ]
        
    def load_nlp_models(self):
        try:
            with open('models/category_model.pkl', 'rb') as f:
                self.cat_model = pickle.load(f)
            with open('models/priority_model.pkl', 'rb') as f:
                self.pri_model = pickle.load(f)
        except Exception as e:
            print("NLP models not found. Please run train_models.py first.")
            
    def load_cv_model(self):
        """Load the HuggingFace ViLT VQA model explicitly (Lighter & Faster)."""
        try:
            from transformers import ViltProcessor, ViltForQuestionAnswering
            # ViLT is ~450MB (much lighter than BLIP's ~1GB) and much faster for VQA
            self.vqa_processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-vqa")
            self.vqa_model = ViltForQuestionAnswering.from_pretrained("dandelin/vilt-b32-finetuned-vqa")
            print("HuggingFace ViLT VQA model loaded successfully.")
        except Exception as e:
            print(f"Failed to load HuggingFace model: {e}")
            self.vqa_processor = None
            self.vqa_model = None

    def predict_text(self, description):
        if not self.cat_model or not self.pri_model:
            return "Unknown", "Low"
            
        category = self.cat_model.predict([description])[0]
        priority = self.pri_model.predict([description])[0]
        return category, priority

    def ask_question(self, img, question):
        """Ask a single question about an image and return the answer + confidence."""
        try:
            inputs = self.vqa_processor(img, question, return_tensors="pt")
            outputs = self.vqa_model(**inputs)
            
            # ViLT gives us direct probabilities (logits) for its vocabulary
            logits = outputs.logits
            idx = logits.argmax(-1).item()
            answer = self.vqa_model.config.id2label[idx]
            
            # Calculate a real confidence score!
            import torch
            probs = torch.nn.functional.softmax(logits, dim=-1)
            score = probs[0, idx].item()
            
            return answer, score
        except Exception as e:
            print(f"VQA error: {e}")
            return "unknown", 0.0

    def analyze_image(self, img_path):
        """
        Analyze an image using the ViLT VQA model by asking descriptive questions.

        Returns:
            answers: list of dicts with 'question', 'answer', 'score', or None on failure.
            summary: human-readable string summarizing the image analysis.
        """
        if getattr(self, 'vqa_model', None) is None or not os.path.exists(img_path):
            return None, "Analysis unavailable"

        try:
            img = Image.open(img_path).convert("RGB")
            
            answers = []
            for question in self.description_questions:
                answer, score = self.ask_question(img, question)
                answers.append({
                    'question': question,
                    'answer': answer,
                    'score': score
                })
            
            # Build a readable summary
            parts = []
            for a in answers:
                parts.append(f"Q: {a['question']}\nA: {a['answer']} ({a['score']*100:.1f}% confidence)")
            summary = "\n".join(parts)
            
            return answers, summary
        except Exception as e:
            print(f"Image analysis error: {e}")
            return None, f"Analysis failed: {e}"

    def verify_image(self, img_path, predicted_category):
        """
        Verify that the uploaded image is relevant to the predicted complaint
        category by asking yes/no questions using ViLT VQA.

        Returns:
            verification_status: "Verified", "Suspicious", or error string
            analysis_summary: human-readable string of VQA results
        """
        if getattr(self, 'vqa_model', None) is None or not os.path.exists(img_path):
            # Fallback when model is unavailable
            if os.path.exists(img_path) and os.path.getsize(img_path) > 1024:
                return "Unverified (model unavailable)", "No analysis — model not loaded"
            return "Suspicious", "No analysis — model not loaded"

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            return "Suspicious", f"Could not open image: {e}"

        # Step 1: Ask category-specific verification questions
        questions = self.category_questions.get(predicted_category, [])
        
        yes_count = 0
        total_count = len(questions)
        verification_details = []
        
        for question in questions:
            answer, score = self.ask_question(img, question)
            is_yes = answer.lower().strip() in ['yes', 'yeah', 'yep', 'true', '1']
            verification_details.append(
                f"{'✅' if is_yes else '❌'} {question} → {answer} ({score*100:.1f}%)"
            )
            if is_yes:
                yes_count += 1

        # Step 2: Ask general description questions for the summary
        description_parts = []
        for question in self.description_questions:
            answer, score = self.ask_question(img, question)
            description_parts.append(f"Q: {question}\nA: {answer} ({score*100:.1f}%)")

        # Build full summary
        summary_lines = ["── Category Verification ──"] + verification_details
        summary_lines.append("")
        summary_lines.append("── Image Description ──")
        summary_lines.extend(description_parts)
        full_summary = "\n".join(summary_lines)

        # Decision: if at least 1 out of the category questions got "yes" → Verified
        if total_count == 0:
            return "Verified", full_summary
        
        if yes_count >= 1:
            return "Verified", full_summary
        else:
            return "Suspicious", full_summary

ai_system = AIEngine()
