![stars](https://img.shields.io/github/stars/bjoerrrn/url-monitoring) ![last_commit](https://img.shields.io/github/last-commit/bjoerrrn/url-monitoring)

# Monitor URLs

This script monitors a list of URLs, checking if they are reachable. If a URL fails 5 times, a notification is sent to a Discord webhook.

## Features
- Checks HTTP/HTTPS URLs for reachability.
- Can verify if a specific keyword exists on the page.
- Alerts are sent to different Discord webhooks per URL.
- Configured via a `.credo` file.
- Runs automatically via `crontab` on a Raspberry Pi.

## Setup & Installation  

### **1️⃣ Install Dependencies**
On a **Raspberry Pi**, run:  
```bash
sudo apt update
sudo apt install python3 python3-pip -y
pip install requests beautifulsoup4 urllib3
```

### **2️⃣ Clone This Repository**
```bash
git clone https://github.com/bjoerrrn/url-monitoring
   cd monitor-urls
```

### **3️⃣ Configure Your Script**

Open monitor_urls.credo (needs to be in the same folder as the script) and set:
```bash
# Description       URL         Webhook_URL                   Optional_Keyword
"test"              http://...  https://...                   "test"
```

### **4️⃣ Run the Script**

Manual Execution
```bash
python3 monitor_urls.py
```

Run Every Minute with Crontab
```bash
crontab -e
```

Add the following line at the bottom:
```bash
* * * * * /usr/bin/python3 /home/pi/url-monitoring/url-monitor.py
```

Save and exit.

### **📡 Expected Output**

📢 Discord Notifications
```
❌ {url}" → Sent when URL is unreachable.
⚠️ {url} MISSING '{keyword}'" → Sent when keyword check fails.
✅ {url}" → Sent when a previously failing URL recovers.
```

### **🤝 Contributing**

Feel free to open issues or pull requests to improve the script! 🚀

if you want to contact me directly, feel free to do so via discord: https://discordapp.com/users/371404709262786561

### **📜 License**

This project is open-source under the [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) License.
