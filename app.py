import csv
import io
import json
import os
import pickle
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from campaign_manager import CampaignManager, CampaignState
from config_manager import load_config, save_config, validate_config
import template_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

campaign_manager = CampaignManager()

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Upload ───────────────────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid CSV: {e}"}), 400

    required = {"name", "email", "pitch_type", "price"}
    if rows:
        missing = required - set(rows[0].keys())
        if missing:
            return jsonify({"success": False, "error": f"Missing columns: {', '.join(missing)}"}), 400

    # Filter rows with email
    leads = [r for r in rows if r.get("email", "").strip()]

    # Load sent log to mark duplicates
    try:
        import email_sender
        sent_log = email_sender.load_sent_log()
    except Exception:
        sent_log = set()

    new_leads = []
    dup_count = 0
    preview = []
    for lead in leads:
        is_dup = lead["email"].strip() in sent_log
        if is_dup:
            dup_count += 1
        else:
            new_leads.append(lead)
        if len(preview) < 10:
            preview.append({
                "name": lead.get("name", ""),
                "email": lead.get("email", ""),
                "pitch_type": lead.get("pitch_type", ""),
                "price": lead.get("price", ""),
                "is_duplicate": is_dup,
            })

    campaign_manager.upload_leads(leads)

    config = load_config()
    delay = config.get("delay_seconds", 30)
    estimated_minutes = round((len(new_leads) * delay) / 60, 1)

    return jsonify({
        "success": True,
        "total_leads": len(leads),
        "new_leads": len(new_leads),
        "duplicate_leads": dup_count,
        "estimated_minutes": estimated_minutes,
        "preview": preview,
    })


# ── Config ───────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def set_config():
    data = request.get_json() or {}
    valid, err = validate_config(data)
    if not valid:
        return jsonify({"success": False, "error": err}), 400
    cfg = load_config()
    if "daily_limit" in data:
        cfg["daily_limit"] = int(data["daily_limit"])
    if "delay_seconds" in data:
        cfg["delay_seconds"] = int(data["delay_seconds"])
    save_config(cfg)
    return jsonify({"success": True, "config": cfg})


# ── Campaign ─────────────────────────────────────────────────────────────────

@app.route("/api/campaign/start", methods=["POST"])
def start_campaign():
    config = load_config()
    data = request.get_json() or {}
    if "daily_limit" in data:
        config["daily_limit"] = int(data["daily_limit"])
    if "delay_seconds" in data:
        config["delay_seconds"] = int(data["delay_seconds"])
    ok, msg = campaign_manager.start_campaign(config)
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    return jsonify({"success": True, "message": msg})


@app.route("/api/campaign/stop", methods=["POST"])
def stop_campaign():
    campaign_manager.stop_campaign()
    return jsonify({"success": True, "message": "Stop signal sent"})


@app.route("/api/progress")
def progress():
    return jsonify(campaign_manager.get_progress())


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/api/history")
def history():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    sent_log_file = "sent_log.json"
    emails = []
    if os.path.exists(sent_log_file):
        try:
            with open(sent_log_file) as f:
                raw = json.load(f)
            # Support both list of strings and list of dicts
            for item in raw:
                if isinstance(item, str):
                    emails.append({"email": item, "timestamp": "—"})
                elif isinstance(item, dict):
                    emails.append(item)
        except Exception:
            pass

    total = len(emails)
    start = (page - 1) * per_page
    end = start + per_page
    page_emails = emails[start:end]

    return jsonify({
        "total_count": total,
        "emails": page_emails,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    })


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/api/auth/status")
def auth_status():
    creds_exist = os.path.exists("credentials.json")
    token_exist = os.path.exists("token.pickle")
    authenticated = False
    email_addr = None

    if token_exist:
        try:
            with open("token.pickle", "rb") as f:
                creds = pickle.load(f)
            if creds and creds.valid:
                authenticated = True
                # Try to get email from id_token
                if hasattr(creds, "id_token") and creds.id_token:
                    email_addr = creds.id_token.get("email")
                if not email_addr:
                    email_addr = "rishi.sawant2005@gmail.com"
        except Exception:
            pass

    return jsonify({
        "authenticated": authenticated,
        "email": email_addr,
        "credentials_exist": creds_exist,
        "token_exist": token_exist,
    })


@app.route("/api/auth/initiate", methods=["POST"])
def auth_initiate():
    try:
        import email_sender
        email_sender.authenticate()
        return jsonify({"success": True, "message": "Authentication complete"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Templates ─────────────────────────────────────────────────────────────────

@app.route("/api/templates")
def get_templates():
    templates = template_manager.load_templates()
    return jsonify({"templates": templates})


@app.route("/api/templates", methods=["POST"])
def create_template():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    
    if not name or not subject or not body:
        return jsonify({"success": False, "error": "Name, subject, and body are required"}), 400
    
    template = template_manager.add_template(name, subject, body)
    return jsonify({"success": True, "template": template})


@app.route("/api/templates/<template_id>", methods=["DELETE"])
def delete_template(template_id):
    success = template_manager.delete_template(template_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Template not found"}), 404


@app.route("/api/templates/<template_id>/set-default", methods=["POST"])
def set_default_template(template_id):
    success = template_manager.set_default_template(template_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Template not found"}), 404


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    try:
        print(f"Starting Email Campaign Manager on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    except OSError as e:
        print(f"Error: Could not start server - {e}")
        sys.exit(1)
