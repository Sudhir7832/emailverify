from flask import Flask, request, jsonify
import smtplib
import dns.resolver
import re
import os

app = Flask(__name__)

# Example list of disposable domains
DISPOSABLE_DOMAINS = [
    "mailinator.com", "10minutemail.com", "temp-mail.org",
    "yopmail.com", "guerrillamail.com", "tempmail.org", "throwawaymail.com"
]

# Common role-based prefixes
ROLE_PREFIXES = ["admin", "info", "support", "contact", "sales", "noreply", "no-reply", "hello", "team"]

def is_valid_syntax(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email.strip()) is not None

def domain_exists(domain):
    try:
        dns.resolver.resolve(domain, 'A')
        return True
    except:
        return False

def has_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except:
        return False

def is_disposable(email):
    domain = email.split("@")[1].lower()
    return domain in DISPOSABLE_DOMAINS

def is_role_based(email):
    local_part = email.split("@")[0].lower()
    return any(local_part.startswith(prefix) for prefix in ROLE_PREFIXES)

# REMOVED: verify_mailbox_exists() — too unreliable and often blocked
# Most professional services (ZeroBounce, Hunter, NeverBounce) don't do deep SMTP checks anymore for this reason.

@app.route("/verify-email", methods=["GET"])
def verify_email():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email query parameter is required"}), 400

    email = email.strip().lower()

    syntax = is_valid_syntax(email)
    domain = email.split("@")[1] if "@" in email and syntax else ""

    domain_ok = domain_exists(domain) if syntax else False
    mx_ok = has_mx_record(domain) if domain_ok else False

    disposable = is_disposable(email)
    role_based = is_role_based(email)

    # Adjusted scoring without mailbox check
    checks_passed = [
        syntax,
        domain_ok,
        mx_ok,
        not disposable,
        not role_based
    ]
    score = 100 if all(checks_passed) else (80 if sum(checks_passed) >= 4 else 50 if sum(checks_passed) >= 3 else 0)
    
    status = "VALID" if score >= 80 else "RISKY" if score >= 50 else "INVALID"

    response = {
        "email": email,
        "validations": {
            "syntax": syntax,
            "domain_exists": domain_ok,
            "mx_records": mx_ok,
            "is_disposable": disposable,
            "is_role_based": role_based
        },
        "score": score,
        "status": status
    }
    return jsonify(response)

# REMOVE the if __name__ == "__main__" block entirely for Railway
# Railway will import and run the 'app' object directly

# Optional: health check endpoint
@app.route("/")
def health():
    return "Email verification service is running!", 200
