import hashlib, json, requests, os
from flask import Blueprint, request, redirect, jsonify, session
from dotenv import load_dotenv
from urllib.parse import urlencode


load_dotenv()
auth_bp = Blueprint('auth', __name__)

CLIENT_ID = os.getenv("FYERS_CLIENT_ID")     # e.g. "ZG5SKFZa61N-100"
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")   # from Fyers dashboard
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")

FYERS_BASE = "https://api-t1.fyers.in/api/v3"
TOKEN_URL = "https://api-t1.fyers.in/api/v3/token"


# ---------------------------
# STEP 1: Redirect to Fyers Login
# ---------------------------
@auth_bp.route("/login")
def login():
    params = {
        "client_id": CLIENT_ID,  # Full client ID with -100
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": "sample_state",
        "scope": "",
        "nonce": "random_nonce"
    }
    auth_url = f"{FYERS_BASE}/generate-authcode?{urlencode(params)}"
    print(f"Redirecting to Fyers auth URL: {auth_url}")
    return redirect(auth_url)


# ---------------------------
# STEP 2: Callback from Fyers (with auth_code)
# ---------------------------
@auth_bp.route("/callback")
def callback():
    auth_code = request.args.get("auth_code")
    if not auth_code:
        return "Authorization failed. No auth_code returned.", 400

    # ✅ Critical Fix: Use the FULL CLIENT_ID (including -100) for appIdHash
    # Do NOT split or remove the suffix
    appIdHash = hashlib.sha256(f"{CLIENT_ID}:{SECRET_KEY}".encode()).hexdigest()
    print("Generated appIdHash:", appIdHash)
    print(f"Using CLIENT_ID: {CLIENT_ID}")

    payload = {
        "grant_type": "authorization_code",
        "appIdHash": appIdHash,
        "code": auth_code
    }

    token_url = f"{FYERS_BASE}/validate-authcode"  # ✅ Correct endpoint
    print("Requesting Token from:", token_url)
    print("Payload:", payload)

    res = requests.post(token_url, json=payload)
    data = res.json()
    print("Token Response:", data)

    if data.get("s") == "ok" and "access_token" in data:
        session["access_token"] = data["access_token"]
        session["refresh_token"] = data.get("refresh_token")

        with open("fyers_token.json", "w") as f:
            json.dump(data, f)

        return redirect("/dashboard")
    else:
        error_msg = data.get("message", "Unknown error")
        return jsonify({"error": error_msg, "response": data}), 400


# ---------------------------
# STEP 3: Endpoint to check stored tokens
# ---------------------------
@auth_bp.route("/token")
def get_token():
    if "access_token" in session:
        return jsonify({
            "access_token": session["access_token"],
            "refresh_token": session.get("refresh_token")
        })
    return jsonify({"error": "No active session"}), 401