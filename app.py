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

# Shared queue for log messages
log_queue = queue.Queue()
is_running = False

# Store user statuses
user_status = {}  # user_id -> {name, status, error, start_time, end_time}

# ---------- Configuration ----------
TEST = {
    "planner": "241",
    "test": "66665557929",
    "test_name": "11th-jee-ct-pt-1"
}

# Users list – add your full list here
USERS = [
    {"user": "26173000217", "name": "TANISHA RATHORE"},
    {"user": "26173000190", "name": "MEET KAUSHIK"},
    # ... include all users
]

HEADLESS = True
AUTO_SUBMIT = True
USE_PROXIES = False
PROXY_LIST = []
# -----------------------------------

def log_message(msg, level="info", user=None, status=None, error=None):
    entry = {
        "type": "log",
        "level": level,
        "message": msg,
        "time": time.strftime("%H:%M:%S")
    }
    if user:
        entry["user"] = user
    if status:
        entry["status"] = status
    if error:
        entry["error"] = error
    log_queue.put(entry)
    print(f"[{entry['time']}] {msg}")

def update_user_status(user_id, name, status, error=None):
    user_status[user_id] = {
        "name": name,
        "status": status,
        "error": error,
        "time": time.strftime("%H:%M:%S")
    }
    log_queue.put({
        "type": "status_update",
        "user_id": user_id,
        "name": name,
        "status": status,
        "error": error,
        "time": time.strftime("%H:%M:%S")
    })

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
        if HEADLESS:
            chrome_options.add_argument("--headless=new")
        temp_profile = os.path.join(tempfile.gettempdir(), f"motion_bulk_{random.randint(1000,9999)}")
        if not os.path.exists(temp_profile):
            os.makedirs(temp_profile)
        chrome_options.add_argument(f"--user-data-dir={temp_profile}")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1920,1080")
        if USE_PROXIES and PROXY_LIST:
            proxy = random.choice(PROXY_LIST)
            chrome_options.add_argument(f"--proxy-server={proxy}")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
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

# ---------- Flask Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_job():
    global is_running
    if is_running:
        return jsonify({"status": "already_running"}), 400
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except:
            break
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
