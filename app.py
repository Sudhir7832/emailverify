from flask import Flask, request, jsonify
import smtplib
import dns.resolver
import re

app = Flask(__name__)

# Example list of disposable domains
DISPOSABLE_DOMAINS = ["mailinator.com", "10minutemail.com", "temp-mail.org", "internxt.com"]

# Common role-based prefixes
ROLE_PREFIXES = ["admin", "info", "support", "contact", "sales", "noreply"]

def is_valid_syntax(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

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
    return local_part in ROLE_PREFIXES

'''def verify_mailbox_exists(email):
    domain = email.split("@")[-1]
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_record = str(records[0].exchange)

        server = smtplib.SMTP(timeout=10)
        server.connect(mx_record)
        server.helo(server.local_hostname)
        server.mail("me@example.com")  # sender email

        code, _ = server.rcpt(email)
        server.quit()
        return code == 250
    except:
        return False
'''
@app.route("/verify-email", methods=["GET"])
def verify_email():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email query parameter is required"}), 400

    syntax = is_valid_syntax(email)
    domain = email.split("@")[1] if "@" in email else ""
    domain_ok = domain_exists(domain) if syntax else False
    mx_ok = has_mx_record(domain) if domain_ok else False
    #mailbox_ok = verify_mailbox_exists(email) if mx_ok else False
    disposable = is_disposable(email)
    role_based = is_role_based(email)

    # Simple scoring system
    score = 100 if all([syntax, domain_ok, mx_ok, not disposable, not role_based]) else 0
    status = "VALID" if score == 100 else "INVALID"

    response = {
        "email": email,
        "validations": {
            "syntax": syntax,
            "domain_exists": domain_ok,
            "mx_records": mx_ok,
            #"mailbox_exists": mailbox_ok,
            "is_disposable": disposable,
            "is_role_based": role_based
        },
        "score": score,
        "status": status
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
