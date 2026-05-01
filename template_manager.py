import json
import os
from typing import List, Dict, Optional

TEMPLATES_FILE = "email_templates.json"

DEFAULT_TEMPLATES = [
    {
        "id": "website-indian",
        "name": "Website Pitch (Indian)",
        "subject": "Quick question about your online presence",
        "body": """Hi {name},

I noticed your business and wanted to reach out. I'm a full-stack developer based in Mumbai, and I specialize in building professional websites that help businesses grow their online presence.

I've recently completed projects for:
- A dental clinic in Mumbai (modern booking system and patient portal)
- A law firm in Mumbai (professional website with case management features)
- An ecommerce business in Mumbai (full online store with payment integration)

I'd love to discuss how I can help your business with a professional website. My rates start at ₹12,000-15,000.

Best regards,
{sender_name}
Full-Stack Developer | Mumbai
Phone: {sender_phone}
Portfolio: {sender_portfolio}""",
        "is_default": True,
    },
    {
        "id": "management-indian",
        "name": "Management Tool Pitch (Indian)",
        "subject": "Are you still managing your operations manually?",
        "body": """Hi {name},

I noticed your business and wanted to reach out. I'm a full-stack developer based in Mumbai, and I specialize in building custom management systems that streamline operations and eliminate manual processes.

I've recently completed projects for:
- A dental clinic in Mumbai (modern booking system and patient portal)
- A law firm in Mumbai (Legal Management System for case tracking and client management)
- An ecommerce business in Mumbai (Business Dashboard for inventory and order management)

I'd love to discuss how I can help automate your business operations with a custom management system. My rates start at ₹40,000+.

Best regards,
{sender_name}
Full-Stack Developer | Mumbai
Phone: {sender_phone}
Portfolio: {sender_portfolio}""",
        "is_default": False,
    },
]


def load_templates() -> List[Dict]:
    if not os.path.exists(TEMPLATES_FILE):
        save_templates(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_TEMPLATES


def save_templates(templates: List[Dict]) -> None:
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)


def get_template_by_id(template_id: str) -> Optional[Dict]:
    templates = load_templates()
    for t in templates:
        if t["id"] == template_id:
            return t
    return None


def get_default_template() -> Optional[Dict]:
    templates = load_templates()
    for t in templates:
        if t.get("is_default"):
            return t
    return templates[0] if templates else None


def set_default_template(template_id: str) -> bool:
    templates = load_templates()
    found = False
    for t in templates:
        if t["id"] == template_id:
            t["is_default"] = True
            found = True
        else:
            t["is_default"] = False
    if found:
        save_templates(templates)
    return found


def add_template(name: str, subject: str, body: str) -> Dict:
    templates = load_templates()
    new_id = f"custom-{len(templates) + 1}"
    new_template = {
        "id": new_id,
        "name": name,
        "subject": subject,
        "body": body,
        "is_default": False,
    }
    templates.append(new_template)
    save_templates(templates)
    return new_template


def delete_template(template_id: str) -> bool:
    templates = load_templates()
    original_len = len(templates)
    templates = [t for t in templates if t["id"] != template_id]
    if len(templates) < original_len:
        save_templates(templates)
        return True
    return False


def format_email(template: Dict, lead: Dict, sender_info: Dict) -> tuple:
    """Format email subject and body with lead and sender info"""
    name = lead.get("name", "")
    if name:
        first_name = name.strip().split()[0]
    else:
        first_name = "there"
    
    replacements = {
        "{name}": first_name,
        "{sender_name}": sender_info.get("name", ""),
        "{sender_phone}": sender_info.get("phone", ""),
        "{sender_portfolio}": sender_info.get("portfolio", ""),
    }
    
    subject = template["subject"]
    body = template["body"]
    
    for key, value in replacements.items():
        subject = subject.replace(key, value)
        body = body.replace(key, value)
    
    return subject, body
