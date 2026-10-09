# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 21:56:51 2026

@author: Asus
"""

import sys
from PIL import Image
from PIL.ExifTags import TAGS
from transformers import pipeline

# Known generator tags and keywords embedded by AI engines
AI_KEYWORDS = [
    "prompt", "negative_prompt", "steps", "sampler", "cfg scale",
    "seed", "model hash", "comfyui", "automatic1111", "midjourney",
    "dall-e", "stablediffusion", "novelai"
]

def check_metadata(image_path: str) -> dict:
    """Inspects file chunks and EXIF data for AI generation artifacts."""
    findings = []
    
    with Image.open(image_path) as img:
        # 1. Inspect PNG text chunks (A1111, ComfyUI, WebUI)
        if img.format == "PNG" and hasattr(img, "text"):
            for key, val in img.text.items():
                val_lower = str(val).lower()
                for kw in AI_KEYWORDS:
                    if kw in val_lower or kw in key.lower():
                        findings.append(f"PNG text chunk '{key}' matches generator keyword '{kw}'")

        # 2. Inspect EXIF tags (JPEG, WebP, TIFF)
        exif_data = img.getexif()
        if exif_data:
            for tag_id, val in exif_data.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                val_lower = str(val).lower()
                for kw in AI_KEYWORDS:
                    if kw in val_lower:
                        findings.append(f"EXIF tag '{tag_name}' matches generator keyword '{kw}'")

    if findings:
        return {
            "is_ai_metadata_detected": True,
            "evidence": list(set(findings))
        }
    return {"is_ai_metadata_detected": False, "evidence": []}


def run_vision_classifier(image_path: str, model_name: str = "dima806/ai_vs_real_image_detection") -> dict:
    """Runs a fine-tuned vision classifier on raw pixels."""
    # Pipeline handles image resizing, normalization, and tensor conversion
    classifier = pipeline("image-classification", model=model_name)
    results = classifier(image_path)
    
    scores = {res["label"].lower(): round(res["score"] * 100, 2) for res in results}
    fake_prob = scores.get("fake", scores.get("ai", 0.0))
    real_prob = scores.get("real", scores.get("human", 0.0))
    
    return {
        "fake_probability": f"{fake_prob}%",
        "real_probability": f"{real_prob}%",
        "prediction": "AI-Generated" if fake_prob > real_prob else "Real / Human-Made"
    }


def verify_image(image_path: str):
    print(f"\n--- Analyzing: {image_path} ---")
    
    # Step 1: Metadata Check
    meta_result = check_metadata(image_path)
    if meta_result["is_ai_metadata_detected"]:
        print("[+] Strong AI Metadata Confirmed (100% Synthetic Origin)")
        for item in meta_result["evidence"]:
            print(f"    - {item}")
        return

    print("[-] No generation metadata found (stripped or captured from camera).")
    print("[*] Running Vision Model Inference...")

    # Step 2: Pixel Classification
    vision_result = run_vision_classifier(image_path)
    print(f"[+] Verdict: {vision_result['prediction']}")
    print(f"    - AI Confidence:   {vision_result['fake_probability']}")
    print(f"    - Real Confidence: {vision_result['real_probability']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        verify_image(sys.argv[1])
    else:
        print("Usage: python verify_image.py <path_to_image>")