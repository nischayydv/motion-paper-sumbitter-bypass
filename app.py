import os
import threading
import queue
import time
import re
import json
import tempfile
import logging
from flask import Flask, render_template, Response, request, jsonify
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Silence verbose logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)

app = Flask(__name__)

# ---------- Global Test Configuration ----------
TEST = {
    "planner": "241",
    "test": "66665557929",
    "test_name": "11th-jee-ct-pt-1"
}

AUTO_SUBMIT = True
CHROMEDRIVER_PATH = None
HEADLESS_MODE = True

# ---------- MongoDB Setup ----------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://nischay419:nischay419@cluster0.z6hynou.mongodb.net/?appName=Cluster0")
try:
    client = MongoClient(MONGO_URI)
    db = client["motion3"]
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

# ---------- Helpers & Database Logic ----------
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

def create_initial_user_results():
    users = get_users()
    results = {}
    for u in users:
        results[u["user"]] = {
            "name": u["name"],
            "status": "idle",
            "error": None,
            "time": "--"
        }
    return results

def get_job_doc():
    initial_results = create_initial_user_results()
    if mongo_available:
        doc = jobs_collection.find_one({"_id": "current"})
        if not doc:
            jobs_collection.insert_one({
                "_id": "current",
                "status": "idle",
                "current_index": 0,
                "results": initial_results
            })
            doc = jobs_collection.find_one({"_id": "current"})
        else:
            stored_results = doc.get("results", {})
            updated = False
            for uid, details in initial_results.items():
                if uid not in stored_results:
                    stored_results[uid] = details
                    updated = True
            if updated:
                jobs_collection.update_one({"_id": "current"}, {"$set": {"results": stored_results}})
                doc["results"] = stored_results
        return doc

    if not job_data.get("results"):
        job_data["results"] = initial_results
    else:
        for uid, details in initial_results.items():
            if uid not in job_data["results"]:
                job_data["results"][uid] = details
    return job_data

def update_job_doc(updates):
    if mongo_available:
        jobs_collection.update_one({"_id": "current"}, {"$set": updates}, upsert=True)
    else:
        job_data.update(updates)

def update_user_status(user_id, name, status, error=None):
    time_str = time.strftime("%H:%M:%S") if status != "idle" else "--"
    if mongo_available:
        jobs_collection.update_one(
            {"_id": "current"},
            {"$set": {f"results.{user_id}": {"name": name, "status": status, "error": error, "time": time_str}}},
            upsert=True
        )
    else:
        job_data["results"][user_id] = {"name": name, "status": status, "error": error, "time": time_str}

def reset_stuck_jobs():
    get_job_doc()
    update_job_doc({"status": "idle"})

reset_stuck_jobs()

# ---------- Logging ----------
log_queue = queue.Queue()

def log_message(msg, level="info", user=None, status=None, error=None):
    entry = {"type": "log", "level": level, "message": msg, "time": time.strftime("%H:%M:%S")}
    if user: entry["user"] = user
    if status: entry["status"] = status
    if error: entry["error"] = error
    log_queue.put(entry)
    print(f"[{entry['time']}] {msg}")

# ---------- Optimized Motion Test Engine ----------
class MotionTestOpener:
    def __init__(self, driver_path=None):
        self.base_url = "https://onlinetestseries.motion.ac.in"
        self.driver_path = driver_path
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/dashboard/student-dashboard.php",
            "X-Requested-With": "XMLHttpRequest"
        })

    def _start_chrome(self):
        if self.driver is not None:
            return self.driver

        chrome_options = Options()
        temp_profile = os.path.join(tempfile.gettempdir(), f"motion_chrome_{time.time()}")
        chrome_options.add_argument(f"--user-data-dir={temp_profile}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Fast loading

        if HEADLESS_MODE:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(self.driver_path) if self.driver_path else Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(25)
        self.driver.implicitly_wait(3)
        return self.driver

    def get_test_controls(self, user, planner, test, name, test_name):
        url = f"{self.base_url}/dashboard/secure/api/getTestControls.php"
        data = {"user": user, "planner": planner, "test": test, "name": name, "test_name": test_name}
        resp = self.session.post(url, data=data, timeout=12)
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

    def get_secure_form(self, user_token, planner, test_id, user, exam):
        url = f"{self.base_url}/dashboard/secure/"
        data = {"user_token": user_token, "planner": planner, "test_id": test_id,
                "user": user, "exam": exam, "form_starttest": ""}
        resp = self.session.post(url, data=data, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", action=re.compile(r"test-landing/index\.php"))
        hidden = {}
        if form:
            for inp in form.find_all("input", type="hidden"):
                name = inp.get("name")
                value = inp.get("value")
                if name and value is not None:
                    hidden[name] = value
        return hidden

    def _handle_fullscreen_modal(self, wait):
        try:
            modal = wait.until(EC.presence_of_element_located((By.ID, "fullscreenmodal")))
            self.driver.execute_script("document.getElementById('fullscreenmodal').remove();")
        except Exception:
            pass

    def process_user_test(self, user_info, planner, test_id, test_name, retries=2):
        user = user_info["user"]
        name = user_info["name"]
        update_user_status(user, name, "processing")
        log_message(f"▶️ Processing: {name} ({user})", user=user)

        for attempt in range(1, retries + 1):
            try:
                controls = self.get_test_controls(user, planner, test_id, name, test_name)
                secure = self.get_secure_form(
                    controls["user_token"], controls["planner"],
                    controls["test_id"], controls["user"], controls["exam"]
                )

                driver = self._start_chrome()
                wait = WebDriverWait(driver, 15)

                driver.get("about:blank")
                html = f"""
                <html>
                <body onload="document.forms[0].submit()">
                    <form method="POST" action="{self.base_url}/dashboard/secure/test-landing/index.php">
                """
                for key, value in secure.items():
                    html += f'<input type="hidden" name="{key}" value="{value}" />\n'
                html += """
                    </form>
                </body>
                </html>
                """
                driver.execute_script("document.write(arguments[0])", html)

                try:
                    wait.until(EC.presence_of_element_located((By.ID, "container")))
                except Exception:
                    pass

                self._handle_fullscreen_modal(wait)

                if AUTO_SUBMIT:
                    submit_btn = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]"))
                    )
                    driver.execute_script("arguments[0].click();", submit_btn)

                    try:
                        finish_btn = WebDriverWait(driver, 4).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Finish Test')]"))
                        )
                        driver.execute_script("arguments[0].click();", finish_btn)
                    except Exception:
                        pass

                log_message(f"✅ Successfully submitted: {name}", user=user)
                update_user_status(user, name, "success")
                return True

            except Exception as e:
                if attempt < retries:
                    log_message(f"⚠️ Retry {attempt}/{retries} for {name}: {e}", level="warning", user=user)
                    self.quit()
                    time.sleep(1)
                else:
                    log_message(f"❌ Failed for {user} ({name}): {e}", level="error", user=user)
                    update_user_status(user, name, "failed", error=str(e))
                    return False
            finally:
                self.quit()

    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

# ---------- Bulk Runner Job ----------
is_running = False
job_lock = threading.Lock()

def run_bulk_job():
    global is_running
    with job_lock:
        if is_running:
            return
        is_running = True

    opener = MotionTestOpener(CHROMEDRIVER_PATH)
    try:
        users = get_users()
        doc = get_job_doc()
        start_index = doc.get("current_index", 0)
        remaining_users = users[start_index:]

        log_message(f"🚀 Starting Bulk Submission from index {start_index} ({len(remaining_users)} left)")
        update_job_doc({"status": "running"})

        for idx, user_info in enumerate(remaining_users, start=start_index):
            if not is_running:
                break
            opener.process_user_test(
                user_info,
                TEST["planner"],
                TEST["test"],
                TEST["test_name"]
            )
            update_job_doc({"current_index": idx + 1})

        update_job_doc({"status": "completed"})
        log_message(f"✅ Bulk job sequence completed.")

    except Exception as e:
        log_message(f"❌ Job error: {e}", level="error")
    finally:
        opener.quit()
        with job_lock:
            is_running = False

# ---------- Endpoints ----------
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

@app.route('/submit_single', methods=['POST'])
def submit_single():
    data = request.get_json() or {}
    user_id = str(data.get("user", "")).strip()
    
    users = get_users()
    user_info = next((u for u in users if u["user"] == user_id), None)
    
    if not user_info:
        return jsonify({"status": "error", "message": "User ID not found"}), 404

    def run_single():
        opener = MotionTestOpener(CHROMEDRIVER_PATH)
        try:
            opener.process_user_test(user_info, TEST["planner"], TEST["test"], TEST["test_name"])
        finally:
            opener.quit()

    threading.Thread(target=run_single, daemon=True).start()
    return jsonify({"status": "queued", "user": user_id})

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json() or {}
    user_id = str(data.get("user", "")).strip()
    name = str(data.get("name", "")).strip().upper()

    if not user_id or not name:
        return jsonify({"status": "error", "message": "User ID and Name are required"}), 400

    users = get_users()
    if any(u["user"] == user_id for u in users):
        return jsonify({"status": "error", "message": "Student ID already exists"}), 400

    users.append({"user": user_id, "name": name})
    
    if mongo_available:
        users_collection.update_one({"_id": "list"}, {"$set": {"users": users}}, upsert=True)
    
    update_user_status(user_id, name, "idle")
    log_message(f"➕ Added new student: {name} ({user_id})")
    
    return jsonify({"status": "success", "user": user_id, "name": name})

@app.route('/reset', methods=['POST'])
def reset_job():
    global is_running
    with job_lock:
        if is_running:
            return jsonify({"status": "cannot_reset", "message": "Job is currently running"}), 400
        
        initial_results = create_initial_user_results()
        if mongo_available:
            jobs_collection.update_one(
                {"_id": "current"},
                {"$set": {"status": "idle", "current_index": 0, "results": initial_results}},
                upsert=True
            )
        else:
            job_data["_id"] = "current"
            job_data["status"] = "idle"
            job_data["current_index"] = 0
            job_data["results"] = initial_results

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
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"
    return Response(stream(), mimetype="text/event-stream")

@app.route('/status')
def status():
    doc = get_job_doc()
    return jsonify(doc.get("results", {}))

@app.route('/job_state')
def job_state():
    doc = get_job_doc()
    return jsonify(doc)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
