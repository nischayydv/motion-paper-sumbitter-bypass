import os
import threading
import queue
import time
import re
import concurrent.futures
from flask import Flask, render_template, Response, request, jsonify
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

app = Flask(__name__)

# ---------- Global Test Configuration ----------
TEST = {
    "planner": "241",
    "test": "66665557929",
    "test_name": "11th-jee-ct-pt-1"
}

# ---------- MongoDB Setup ----------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://nischay419:nischay419@cluster0.z6hynou.mongodb.net/?appName=Cluster0")
try:
    client = MongoClient(MONGO_URI)
    db = client["motion"]
    jobs_collection = db["jobs"]
    users_collection = db["users"]
    mongo_available = True
except Exception as e:
    print(f"⚠️ MongoDB connection failed: {e}. Using in-memory fallback.")
    mongo_available = False
    jobs_collection = None
    users_collection = None
    job_data = {"_id": "current", "status": "idle", "current_index": 0, "results": {}}
    user_list = []

# ---------- Startup Clean-up ----------
def reset_stuck_jobs():
    if mongo_available:
        doc = jobs_collection.find_one({"_id": "current"})
        if doc and doc.get("status") == "running":
            jobs_collection.update_one({"_id": "current"}, {"$set": {"status": "idle"}})
            print("✅ Reset stuck job status to idle.")
    else:
        if job_data.get("status") == "running":
            job_data["status"] = "idle"
            print("✅ Reset stuck job status to idle.")

reset_stuck_jobs()

# ---------- Default User List ----------
DEFAULT_USERS = [
    {"user": "26173000217", "name": "TANISHA RATHORE"},
    {"user": "26173000190", "name": "MEET KAUSHIK"},
    {"user": "26173000201", "name": "ANUJ YADAV"},
    {"user": "26173000210", "name": "DAKSH"},
    {"user": "26173000184", "name": "YATHARTH"},
    {"user": "26173000191", "name": "CHIRAG YADAV"},
    {"user": "26173000237", "name": "DIKSHA"},
    {"user": "26173000200", "name": "DIVYA YADAV"},
    {"user": "26173000205", "name": "DARSHIL YADAV"},
    {"user": "26173000225", "name": "ABHISHEK"},
    {"user": "26173000289", "name": "DISHANT"},
    {"user": "26173000193", "name": "KAVYANSHU"},
    {"user": "26173000177", "name": "MAYANK"},
    {"user": "26173000213", "name": "AARAV THAKRAN"},
    {"user": "26173000449", "name": "JESSICA"},
    {"user": "26173000189", "name": "HIMANSHU MUDGIL"},
    {"user": "26173000186", "name": "ABHI"},
    {"user": "26173000196", "name": "DHRUVIKA"},
    {"user": "26173000286", "name": "JANVI VASHISTH"},
    {"user": "26173000450", "name": "BABY"},
    {"user": "26173000206", "name": "RUPESH YADAV"},
    {"user": "26173000207", "name": "AYUSH TIWARI"},
    {"user": "26173000227", "name": "DEEPIKA ALWARIA"},
    {"user": "26173000215", "name": "ANSHIKA YADAV"},
    {"user": "26173000269", "name": "DEV RAJ KUMAR"},
    {"user": "26173000259", "name": "SHIVAM KUMAR"},
    {"user": "26173000285", "name": "KANIKA YADAV"},
    {"user": "26173000002", "name": "AKSHITA YADAV"},
    {"user": "26173000260", "name": "SHUBHAM KUMAR"},
    {"user": "26173000219", "name": "DEEPANSHU YADAV"},
    {"user": "26173000216", "name": "RONAK SAMBHARIA"},
    {"user": "26173000199", "name": "CHIRAG KUMAR"},
    {"user": "26173000287", "name": "VANSH GAUR"},
    {"user": "26173000204", "name": "ISHU THAKRAN"},
    {"user": "26173000226", "name": "RIYA"},
    {"user": "26173000448", "name": "SUHANI BHAMASRA"},
    {"user": "26173000283", "name": "RISHABH"},
    {"user": "26173000214", "name": "AYUSH YADAV"},
    {"user": "26173000505", "name": "LAKSHITA"},
    {"user": "26173000809", "name": "LAKSHAY"},
    {"user": "26173000209", "name": "HARSH"},
    {"user": "26173000278", "name": "LAKSHAY"},
    {"user": "26173000255", "name": "PRINCE"},
    {"user": "26173000179", "name": "DAKSH"},
    {"user": "26173000223", "name": "CHHAVI"},
    {"user": "26173000804", "name": "DAKSH YADAV"},
    {"user": "26173000292", "name": "VAIBHAV"},
    {"user": "26173000198", "name": "GRISHIKA YADAV"},
    {"user": "26173000187", "name": "AMANDEEP"},
    {"user": "26173000291", "name": "BHAVESH"},
    {"user": "26173000182", "name": "JAYANT YADAV"},
    {"user": "26173000228", "name": "NIKITA YADAV"},
    {"user": "26173000221", "name": "PRATYKSH YADAV"},
    {"user": "26173000277", "name": "SAIJIYA"},
    {"user": "26173000211", "name": "ANSHU"},
    {"user": "26173000488", "name": "PARTEEK SINGH"},
    {"user": "26173000477", "name": "NITIN"},
    {"user": "26173000183", "name": "NILESH VASHISTHA"},
    {"user": "26173000478", "name": "SOMAY"},
    {"user": "26173000195", "name": "AAKANSHA"},
    {"user": "26173000486", "name": "TARUN"},
    {"user": "26173000224", "name": "JATIN KUMAR"},
    {"user": "26173000452", "name": "SHOURYA DABAS"},
    {"user": "26173000220", "name": "DHRUV CHAUHAN"},
    {"user": "26173000212", "name": "MAYANK"},
    {"user": "26173000815", "name": "SUMIT"},
    {"user": "26173000180", "name": "DIPANSHU"},
    {"user": "26173000022", "name": "YASHIKA YADAV"},
    {"user": "26173000818", "name": "KAPIL"},
    {"user": "26173000435", "name": "TANUJ"},
    {"user": "26173000188", "name": "VARSHA"},
    {"user": "26173000246", "name": "MAHI"},
    {"user": "26173000249", "name": "TANISHA"},
    {"user": "26173000806", "name": "VANSH SONI"},
    {"user": "26173000203", "name": "KESHAV YADAV"},
    {"user": "26173000387", "name": "MAHAK CHAUHAN"},
    {"user": "26173000388", "name": "NANCY"},
    {"user": "26173000817", "name": "PRABHAT"},
    {"user": "26173000194", "name": "RAHUL YADAV"},
    {"user": "26173000181", "name": "SHIVANSHU KUMAR"},
    {"user": "26173000812", "name": "TARUN"},
    {"user": "26173000218", "name": "NAITIK CHAUHAN"},
    {"user": "26173000241", "name": "AAYUSHI"},
    {"user": "26173000185", "name": "ISHIKA"},
    {"user": "26173000047", "name": "LAKSHAY VERMA"},
    {"user": "26173000813", "name": "PARUL"}
]

# ---------- Helper Functions ----------
def get_users():
    if mongo_available:
        doc = users_collection.find_one({"_id": "list"})
        if not doc:
            users_collection.insert_one({"_id": "list", "users": DEFAULT_USERS})
            return DEFAULT_USERS
        return doc.get("users", DEFAULT_USERS)
    else:
        if not user_list:
            user_list.extend(DEFAULT_USERS)
        return user_list

def get_job_doc():
    if mongo_available:
        doc = jobs_collection.find_one({"_id": "current"})
        if not doc:
            jobs_collection.insert_one({"_id": "current", "status": "idle", "current_index": 0, "results": {}})
            doc = jobs_collection.find_one({"_id": "current"})
        return doc
    return job_data

def update_job_doc(updates):
    if mongo_available:
        jobs_collection.update_one({"_id": "current"}, {"$set": updates}, upsert=True)
    else:
        job_data.update(updates)

def update_user_status(user_id, name, status, error=None):
    if mongo_available:
        jobs_collection.update_one(
            {"_id": "current"},
            {"$set": {f"results.{user_id}": {"name": name, "status": status, "error": error, "time": time.strftime("%H:%M:%S")}}},
            upsert=True
        )
    else:
        job_data["results"][user_id] = {"name": name, "status": status, "error": error, "time": time.strftime("%H:%M:%S")}

# ---------- Logging ----------
log_queue = queue.Queue()

def log_message(msg, level="info", user=None, status=None, error=None):
    entry = {"type": "log", "level": level, "message": msg, "time": time.strftime("%H:%M:%S")}
    if user: entry["user"] = user
    if status: entry["status"] = status
    if error: entry["error"] = error
    log_queue.put(entry)
    print(f"[{entry['time']}] {msg}")

# ---------- API Extractor Functions ----------
def get_test_controls(session, user, planner, test, name, test_name):
    url = "https://onlinetestseries.motion.ac.in/dashboard/secure/api/getTestControls.php"
    data = {"user": user, "planner": planner, "test": test, "name": name, "test_name": test_name}
    resp = session.post(url, data=data, timeout=10)
    resp.raise_for_status()
    json_resp = resp.json()
    
    if json_resp.get("error") != 0:
        raise Exception(f"API Error: {json_resp.get('msg')}")
        
    soup = BeautifulSoup(json_resp.get("data", ""), "html.parser")
    form = soup.find("form")
    hidden = {}
    if form:
        for inp in form.find_all("input", type="hidden"):
            name_attr = inp.get("name")
            value_attr = inp.get("value")
            if name_attr and value_attr is not None:
                hidden[name_attr] = value_attr
    return hidden

def get_secure_form(session, user_token, planner, test_id, user, exam):
    url = "https://onlinetestseries.motion.ac.in/dashboard/secure/"
    data = {
        "user_token": user_token,
        "planner": planner,
        "test_id": test_id,
        "user": user,
        "exam": exam,
        "form_starttest": ""
    }
    resp = session.post(url, data=data, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", action=re.compile(r"test-landing/index\.php"))
    hidden = {}
    if form:
        for inp in form.find_all("input", type="hidden"):
            name_attr = inp.get("name")
            value_attr = inp.get("value")
            if name_attr and value_attr is not None:
                hidden[name_attr] = value_attr
    return hidden

# ---------- Fast Concurrent API Submission ----------
def submit_user_api(user_info, planner, test_id, test_name):
    user = user_info["user"]
    name = user_info["name"]
    update_user_status(user, name, "processing")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://onlinetestseries.motion.ac.in/dashboard/student-dashboard.php",
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        log_message(f"▶️ Fast API submission: {name} ({user})", user=user)

        # Step 1: Call getTestControls.php
        controls = get_test_controls(session, user, planner, test_id, name, test_name)
        user_token = controls.get("user_token")
        if not user_token:
            raise Exception("Could not extract user_token from getTestControls.php")

        # Step 2: Call secure form verification
        secure_data = get_secure_form(
            session,
            user_token,
            controls.get("planner", planner),
            controls.get("test_id", test_id),
            controls.get("user", user),
            controls.get("exam", test_name)
        )

        # Step 3: Initialize landing session
        landing_url = "https://onlinetestseries.motion.ac.in/dashboard/secure/test-landing/index.php"
        resp_landing = session.post(landing_url, data=secure_data, timeout=10)
        resp_landing.raise_for_status()

        # Step 4: Direct test completion submission
        submit_url = "https://onlinetestseries.motion.ac.in/dashboard/secure/test-landing/submit_test.php"
        submit_payload = {
            "user": user,
            "test_id": test_id,
            "user_token": user_token,
            "status": "completed"
        }
        res_submit = session.post(submit_url, data=submit_payload, timeout=10)

        if res_submit.status_code == 200:
            log_message(f"✅ Submitted successfully via API for {name}", user=user)
            update_user_status(user, name, "success")
        else:
            raise Exception(f"HTTP Error {res_submit.status_code}")

    except Exception as e:
        log_message(f"❌ Error for {user} ({name}): {e}", level="error", user=user)
        update_user_status(user, name, "failed", error=str(e))

# ---------- Concurrent Job Runner ----------
is_running = False
job_lock = threading.Lock()
MAX_WORKERS = 10  # Run 10 requests in parallel

def run_bulk_job():
    global is_running
    with job_lock:
        if is_running:
            return
        is_running = True
    try:
        users = get_users()
        doc = get_job_doc()
        start_index = doc.get("current_index", 0)
        remaining_users = users[start_index:]
        total = len(users)

        log_message(f"🚀 Launching fast API bulk job ({len(remaining_users)} users remaining using {MAX_WORKERS} threads)")
        update_job_doc({"status": "running"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    submit_user_api, 
                    u, 
                    TEST["planner"], 
                    TEST["test"], 
                    TEST["test_name"]
                ): idx for idx, u in enumerate(remaining_users, start=start_index)
            }

            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                update_job_doc({"current_index": idx + 1})

        update_job_doc({"status": "completed"})
        success = sum(1 for r in get_job_doc().get("results", {}).values() if r.get("status") == "success")
        log_message(f"✅ Bulk job finished. Success: {success}/{total}")

    except Exception as e:
        log_message(f"❌ Job crashed: {e}", level="error")
    finally:
        with job_lock:
            is_running = False

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_job():
    global is_running
    with job_lock:
        if is_running:
            return jsonify({"status": "already_running"}), 400
        doc = get_job_doc()
        if doc.get("status") == "running":
            update_job_doc({"status": "idle"})
        thread = threading.Thread(target=run_bulk_job)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "started"})

@app.route('/reset', methods=['POST'])
def reset_job():
    global is_running
    with job_lock:
        if is_running:
            return jsonify({"status": "cannot_reset", "message": "Job is currently running"}), 400
        if mongo_available:
            jobs_collection.delete_one({"_id": "current"})
        else:
            job_data.clear()
            job_data["_id"] = "current"
            job_data["status"] = "idle"
            job_data["current_index"] = 0
            job_data["results"] = {}
        
        while not log_queue.empty():
            try:
                log_queue.get_nowait()
            except queue.Empty:
                break
        return jsonify({"status": "reset"})

@app.route('/logs')
def logs():
    def stream():
        while True:
            try:
                msg = log_queue.get(timeout=1)
                yield f"data: {msg}\n\n"
            except queue.Empty:
                yield f"data: {{'heartbeat': true}}\n\n"
    return Response(stream(), mimetype="text/event-stream")

@app.route('/status')
def status():
    doc = get_job_doc()
    return jsonify(doc.get("results", {}))

@app.route('/job_state')
def job_state():
    doc = get_job_doc()
    return jsonify(doc)

@app.route('/check')
def check():
    return jsonify({
        "mongo_status": mongo_available,
        "max_workers": MAX_WORKERS,
        "engine": "Concurrent Direct HTTP API Engine"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
