"""Together AI integration for paid mode.

Sends invoice page images (base64) to a vision-capable model and returns parsed JSON.
Environment variables (see .env.example):
- TOGETHER_API_KEY
- TOGETHER_MODEL
- TOGETHER_INFERENCE_URL
"""

import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct")
TOGETHER_INFERENCE_URL = os.getenv("TOGETHER_INFERENCE_URL", "https://api.together.xyz/v1/chat/completions")

PROMPT = """You are an expert invoice parser. Extract the following fields from the invoice page image text. Return ONLY valid JSON with this schema exactly:

{
  "vendor_name": "",
  "invoice_number": "",
  "invoice_date": "",
  "due_date": "",
  "bill_to": "",
  "line_items": [
      {"description": "", "quantity": "", "unit_price": "", "total_price": ""}
  ],
  "subtotal": "",
  "tax": "",
  "grand_total": "",
  "payment_info": ""
}

If a field is missing, use empty string or empty list. Return strictly JSON only.
"""

def extract_invoice_with_together(image_path: str) -> dict:
    """Send a single invoice image to Together AI (vision-capable) and parse JSON result.

    Returns a dict matching the project invoice schema or a mostly-empty dict with an "error" key on failure.
    """
    if not TOGETHER_API_KEY:
        raise EnvironmentError("TOGETHER_API_KEY is not set in environment.")

    # Convert image to base64 for Together AI API
    import base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Together AI Chat Completions API format
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    try:
        resp = requests.post(TOGETHER_INFERENCE_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        # Return a minimal empty structure with error noted (so pipeline continues)
        error_msg = str(e)
        try:
            if 'resp' in locals():
                error_msg += " | " + resp.text
        except:
            pass
        return {"vendor_name":"", "invoice_number":"", "invoice_date":"", "due_date":"", "bill_to":"", "line_items":[], "subtotal":"", "tax":"", "grand_total":"", "payment_info":"", "error": error_msg}

    try:
        response_data = resp.json()
        
        # Together AI returns response in choices[0].message.content format
        if "choices" in response_data and len(response_data["choices"]) > 0:
            content = response_data["choices"][0]["message"]["content"]
            
            # Try to parse the content as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                    
        # If no valid JSON found, return error
        return {"vendor_name":"", "invoice_number":"", "invoice_date":"", "due_date":"", "bill_to":"", "line_items":[], "subtotal":"", "tax":"", "grand_total":"", "payment_info":"", "error": "No valid JSON found in response"}
        
    except Exception as e:
        # final fallback empty structure
        return {"vendor_name":"", "invoice_number":"", "invoice_date":"", "due_date":"", "bill_to":"", "line_items":[], "subtotal":"", "tax":"", "grand_total":"", "payment_info":"", "error": f"Response parsing error: {str(e)}"}
