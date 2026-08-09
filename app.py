import os
import threading
import queue
import time
import random
import sys
import re
import tempfile
from flask import Flask, render_template, Response, request, jsonify
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

log_queue = queue.Queue()
is_running = False
user_status = {}

TEST = {
    "planner": "241",
    "test": "66665557929",
    "test_name": "11th-jee-ct-pt-1"
}

# Your full user list (add all users)
# Users list
USERS = [
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

HEADLESS = True
AUTO_SUBMIT = True
USE_PROXIES = False
PROXY_LIST = []

def log_message(msg, level="info", user=None, status=None, error=None):
    entry = {"type": "log", "level": level, "message": msg, "time": time.strftime("%H:%M:%S")}
    if user: entry["user"] = user
    if status: entry["status"] = status
    if error: entry["error"] = error
    log_queue.put(entry)
    print(f"[{entry['time']}] {msg}")

def update_user_status(user_id, name, status, error=None):
    user_status[user_id] = {"name": name, "status": status, "error": error, "time": time.strftime("%H:%M:%S")}
    log_queue.put({"type": "status_update", "user_id": user_id, "name": name, "status": status, "error": error, "time": time.strftime("%H:%M:%S")})

def get_test_controls(user, planner, test, name, test_name):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Origin": "https://onlinetestseries.motion.ac.in",
        "Referer": "https://onlinetestseries.motion.ac.in/dashboard/student-dashboard.php",
        "X-Requested-With": "XMLHttpRequest"
    })
    url = "https://onlinetestseries.motion.ac.in/dashboard/secure/api/getTestControls.php"
    data = {"user": user, "planner": planner, "test": test, "name": name, "test_name": test_name}
    resp = session.post(url, data=data)
    resp.raise_for_status()
    json_resp = resp.json()
    if json_resp.get("error") != 0:
        raise Exception(json_resp.get("msg"))
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

def get_secure_form(user_token, planner, test_id, user, exam):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Origin": "https://onlinetestseries.motion.ac.in",
        "Referer": "https://onlinetestseries.motion.ac.in/dashboard/student-dashboard.php",
        "X-Requested-With": "XMLHttpRequest"
    })
    url = "https://onlinetestseries.motion.ac.in/dashboard/secure/"
    data = {"user_token": user_token, "planner": planner, "test_id": test_id,
            "user": user, "exam": exam, "form_starttest": ""}
    resp = session.post(url, data=data)
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

def submit_user(user, name, planner, test, test_name):
    update_user_status(user, name, "processing")
    try:
        log_message(f"▶️ Processing: {name} ({user})", user=user)
        controls = get_test_controls(user, planner, test, name, test_name)
        secure = get_secure_form(controls["user_token"], controls["planner"],
                                 controls["test_id"], controls["user"], controls["exam"])

        chrome_options = Options()
        # Set Chrome binary location (Render installs Chrome here)
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        if HEADLESS:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        if USE_PROXIES and PROXY_LIST:
            proxy = random.choice(PROXY_LIST)
            chrome_options.add_argument(f"--proxy-server={proxy}")

        # Use webdriver-manager to automatically download and use the correct driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        wait = WebDriverWait(driver, 30)

        driver.get("about:blank")
        html = f"""
        <html>
        <body onload="document.forms[0].submit()">
            <form method="POST" action="https://onlinetestseries.motion.ac.in/dashboard/secure/test-landing/index.php">
        """
        for key, value in secure.items():
            html += f'<input type="hidden" name="{key}" value="{value}" />\n'
        html += """
            </form>
            <script>
                setTimeout(function() { document.forms[0].submit(); }, 100);
            </script>
        </body>
        </html>
        """
        driver.execute_script("document.write(arguments[0])", html)

        wait.until(EC.presence_of_element_located((By.ID, "container")))
        log_message(f"✅ Test page loaded for {name}", user=user)

        if AUTO_SUBMIT:
            try:
                try:
                    modal = driver.find_element(By.ID, "fullscreenmodal")
                    if modal.is_displayed():
                        driver.execute_script("document.getElementById('fullscreenmodal').remove();")
                        time.sleep(1)
                except:
                    pass

                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]")))
                submit_btn.click()
                log_message(f"🔘 Submit clicked for {name}", user=user)

                try:
                    finish_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Finish Test')]")))
                    finish_btn.click()
                    log_message(f"✅ Test submitted successfully for {name}", user=user)
                    update_user_status(user, name, "success")
                except:
                    log_message(f"ℹ️ No confirmation modal for {name} – may still be submitted", user=user)
                    update_user_status(user, name, "success")
            except Exception as e:
                log_message(f"⚠️ Auto-submit failed for {name}: {e}", level="warning", user=user)
                update_user_status(user, name, "failed", error=str(e))
        else:
            update_user_status(user, name, "opened")

        driver.quit()
        time.sleep(random.randint(2, 5))
    except Exception as e:
        log_message(f"❌ Error for {user} ({name}): {e}", level="error", user=user)
        update_user_status(user, name, "failed", error=str(e))

def run_bulk_job():
    global is_running
    is_running = True
    for u in USERS:
        user_status[u["user"]] = {"name": u["name"], "status": "pending", "error": None, "time": time.strftime("%H:%M:%S")}
    log_message(f"🚀 Starting bulk submission for {len(USERS)} users")
    for u in USERS:
        submit_user(u["user"], u["name"], TEST["planner"], TEST["test"], TEST["test_name"])
    success = sum(1 for s in user_status.values() if s["status"] == "success")
    total = len(USERS)
    log_message(f"✅ Bulk job finished. Success: {success}/{total}")
    is_running = False

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_job():
    global is_running
    if is_running:
        return jsonify({"status": "already_running"}), 400
    while not log_queue.empty():
        try: log_queue.get_nowait()
        except: break
    user_status.clear()
    thread = threading.Thread(target=run_bulk_job)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "started"})

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
    return jsonify(user_status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
