# Guide: Automating Any Python Script with Task Scheduler & GitHub Actions

A reusable guide for setting up automated, scheduled execution of any Python script — both locally on Windows and in the cloud via GitHub Actions.

---

## Part 1: Windows Task Scheduler (Local Automation)

Use this when your script needs to run from your own machine (e.g., websites that block datacenter IPs, scripts that need local files, or scripts that open a browser).

### Step 1: Create a Batch File

Create a file called `run_script.bat` in your project folder:

```bat
@echo off
cd /d "C:\path\to\your\project"
python your_script.py >> script_log.txt 2>&1
```

- `cd /d` ensures it switches to the correct drive and directory
- `>> script_log.txt 2>&1` saves all output (including errors) to a log file

### Step 2: Open Task Scheduler

Press `Win + S`, type **Task Scheduler**, and open it.

### Step 3: Create the Task

1. Click **"Create Basic Task"** in the right panel
2. **Name**: Give it a descriptive name (e.g., `MyScriptRunner`)
3. **Trigger**: Choose your schedule:
   - **Daily** — runs once a day at a set time
   - **Weekly** — runs on specific days of the week
   - **When the computer starts** — runs on boot
   - **When I log on** — runs when you sign in
4. **Time**: Set when you want it to run (e.g., `08:00 AM`)
5. **Action**: Select **"Start a program"**
6. **Program/script**: Browse to your `.bat` file

### Step 4: Advanced Settings (Optional but Recommended)

After clicking Finish, find your task in the list, right-click it → **Properties**:

| Setting | Where to Find | What It Does |
|---|---|---|
| **Wake the computer** | Conditions tab | Wakes PC from sleep to run the task |
| **Run task ASAP if missed** | Settings tab | Runs when PC turns on if it missed the scheduled time |
| **Run whether logged on or not** | General tab | Runs even when PC is locked (requires Windows password) |
| **Stop if runs longer than** | Settings tab | Kills the script if it hangs (set to 30 minutes) |

### Step 5: Test It

Right-click your task in the list → **Run**. Check your `script_log.txt` to verify it worked.

### Troubleshooting

| Problem | Fix |
|---|---|
| Script doesn't run | Make sure Python is in your system PATH. Run `where python` in cmd to check |
| "Access denied" errors | Don't use "Run whether logged on or not" — leave the default |
| Script runs but browser doesn't open | Task Scheduler runs in the background. Add `--headed` flag if your script supports it |
| Log file is empty | Check the `.bat` file path is correct. Try running the `.bat` file manually first |

---

## Part 2: GitHub Actions (Cloud Automation)

Use this when your script can run from any server (e.g., API calls, data processing, notifications, web scraping of sites that don't block datacenter IPs).

### Step 1: Create the Workflow File

Create `.github/workflows/run_script.yml` in your repository:

```yaml
name: Scheduled Script Runner

on:
  schedule:
    # Cron syntax: minute hour day month weekday
    # Examples:
    #   '0 2 * * *'    → Every day at 2:00 AM UTC
    #   '30 8 * * 1-5' → Weekdays at 8:30 AM UTC
    #   '0 */6 * * *'  → Every 6 hours
    - cron: '30 2 * * *'
  workflow_dispatch: # Adds a manual "Run workflow" button in the Actions tab

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run the script
      env:
        # Pull secrets from GitHub repository settings
        MY_SECRET_1: ${{ secrets.MY_SECRET_1 }}
        MY_SECRET_2: ${{ secrets.MY_SECRET_2 }}
      run: python your_script.py
```

### Step 2: Add Secrets (for passwords, API keys, etc.)

1. Go to your repository on GitHub.com
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Enter a **Name** (e.g., `MY_SECRET_1`) and the **Secret value**
5. Click **"Add secret"**

In your Python script, access them via:
```python
import os
my_secret = os.getenv("MY_SECRET_1")
```

### Step 3: Trigger Manually

1. Go to the **Actions** tab in your repo
2. Click your workflow name on the left sidebar
3. Click **"Run workflow"** → **"Run workflow"**

### Step 4: Check Logs

Click on any workflow run → click the job name → expand each step to see terminal output.

### Cron Schedule Cheat Sheet

| Schedule | Cron Expression | Notes |
|---|---|---|
| Every day at 8 AM IST | `30 2 * * *` | IST = UTC + 5:30 |
| Every day at midnight IST | `30 18 * * *` | Previous day 6:30 PM UTC |
| Weekdays at 9 AM IST | `30 3 * * 1-5` | Mon-Fri only |
| Every 6 hours | `0 */6 * * *` | 4 times a day |
| Every Monday at 10 AM IST | `30 4 * * 1` | Weekly |

> ⚠️ **GitHub Actions cron uses UTC time.** To convert IST to UTC, subtract 5 hours 30 minutes.

### Common Additions

#### If your script needs a browser (Playwright):
```yaml
    - name: Install Playwright browsers
      run: playwright install chromium --with-deps
```

#### If your script needs a browser (Selenium):
```yaml
    - name: Install Chrome
      run: |
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
```

#### Upload files generated by the script:
```yaml
    - name: Upload output files
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: script-output
        path: output/
        if-no-files-found: ignore
```

---

## Which Method Should I Use?

| Criteria | Task Scheduler | GitHub Actions |
|---|---|---|
| **Cost** | Free | Free (2,000 min/month) |
| **Needs PC on?** | Yes (or in sleep) | No |
| **Works with browser automation?** | ✅ Always | ⚠️ Only if the site doesn't block datacenter IPs |
| **Access local files?** | ✅ Yes | ❌ No (only repo files) |
| **Runs if PC is off?** | ❌ No (catches up when turned on) | ✅ Yes |
| **Needs internet?** | ✅ Yes | ✅ Yes |
| **Setup difficulty** | Easy | Easy |

### Recommendation

- **Browser automation on protected sites** (Naukri, LinkedIn, etc.) → **Task Scheduler**
- **API calls, data processing, notifications** → **GitHub Actions**
- **Need 100% uptime + browser automation** → Use a cloud VPS (Oracle Cloud Free Tier, AWS EC2, etc.)



++++++++++++++++++++++ 
full test:
cd c:\Users\aks\Documents\Github\career\monitor
.\run_monitor.bat
