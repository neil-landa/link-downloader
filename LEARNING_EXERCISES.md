# Learning Exercises - Hands-On Practice

These exercises will help you understand the code by modifying it yourself. Start with the easy ones and work your way up!

## 🟢 Beginner Exercises

### Exercise 1: Change the Button Text
**Goal:** Understand how HTML and CSS work together

**Task:** Change "Download All" to "Convert to Audio"

**Where:** `index.html`, line ~179

**What you'll learn:** How HTML text affects what users see

---

### Exercise 2: Change the Color Scheme
**Goal:** Understand CSS styling

**Task:** Change the primary color from blue to green

**Where:** `css/general.css`, look for `#2949ab` and `#213a89`

**Steps:**
1. Find all instances of `#2949ab` (the blue color)
2. Replace with a green color like `#2d8659`
3. Find `#213a89` (darker blue) and replace with darker green like `#1f5c3f`
4. Refresh your browser to see changes

**What you'll learn:** How CSS colors work, how to find and replace

---

### Exercise 3: Add Console Logging
**Goal:** Understand JavaScript debugging

**Task:** Add `console.log()` statements to see what's happening

**Where:** `js/script.js`, in the form submission handler

**Add these lines:**
```javascript
console.log("Form submitted!");
console.log("Form data:", formData);
console.log("Number of links:", links.length);
```

**What you'll learn:** How to debug JavaScript, what data is being sent

---

### Exercise 4: Change the Loading Message
**Goal:** Understand JavaScript DOM manipulation

**Task:** Change "Downloading... Please wait" to "Processing your links..."

**Where:** `js/script.js`, find the line with `"Downloading... Please wait"`

**What you'll learn:** How JavaScript changes page content dynamically

---

## 🟡 Intermediate Exercises

### Exercise 5: Add Link Validation
**Goal:** Understand form validation

**Task:** Check if URLs are valid before submitting

**Where:** `js/script.js`, before the `fetch()` call

**Add this code:**
```javascript
// Validate URLs
const invalidLinks = [];
for (let i = 1; i <= 10; i++) {
    const input = document.querySelector(`#link-${i}`);
    if (input.value && !input.value.startsWith('http')) {
        invalidLinks.push(`Link ${i}`);
    }
}

if (invalidLinks.length > 0) {
    alert(`Invalid URLs in: ${invalidLinks.join(', ')}`);
    submitBtn.disabled = false;
    return;
}
```

**What you'll learn:** Form validation, JavaScript loops, conditional logic

---

### Exercise 6: Show Link Count
**Goal:** Understand DOM manipulation and user feedback

**Task:** Display how many links the user entered

**Where:** `js/script.js`, after collecting form data

**Add this:**
```javascript
const linkCount = Array.from(formData.values()).filter(v => v.trim() !== '').length;
console.log(`User entered ${linkCount} links`);
```

**What you'll learn:** Array methods, filtering data, counting

---

### Exercise 7: Add Download Timeout
**Goal:** Understand error handling

**Task:** Add a timeout so downloads don't hang forever

**Where:** `js/script.js`, in the fetch call

**Modify the fetch:**
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

const response = await fetch("/download", {
    method: "POST",
    body: formData,
    signal: controller.signal
});

clearTimeout(timeoutId);
```

**What you'll learn:** Request timeouts, AbortController API

---

### Exercise 8: Change Audio Format
**Goal:** Understand command-line arguments

**Task:** Change from M4A to MP3 format

**Where:** `app.py`, in the `download_audio()` function

**Change:**
```python
'--audio-format', 'mp3',  # Instead of 'm4a'
```

**Note:** You might need to install ffmpeg for MP3 conversion

**What you'll learn:** How command-line tools work, format options

---

## 🟠 Advanced Exercises

### Exercise 9: Add Progress Indicator
**Goal:** Understand async operations and UI updates

**Task:** Show a progress bar during download

**Steps:**
1. Add HTML for progress bar in `index.html`:
```html
<div id="progress" style="display: none;">
    <div style="background: #213a89; height: 4px; width: 0%; transition: width 0.3s;"></div>
</div>
```

2. In JavaScript, show and update it:
```javascript
const progressDiv = document.getElementById('progress');
progressDiv.style.display = 'block';
// Update width based on progress
```

**What you'll learn:** UI updates, progress tracking, CSS animations

---

### Exercise 10: Download Files Individually
**Goal:** Understand server responses and file handling

**Task:** Instead of ZIP, download each file separately

**Where:** `app.py`, modify the download route

**Change the response:**
```python
# Instead of creating ZIP, send first file
if all_files:
    return send_file(all_files[0], as_attachment=True)
```

**Challenge:** Send multiple files (requires more complex response)

**What you'll learn:** File serving, multiple responses, HTTP limitations

---

### Exercise 11: Add Download History
**Goal:** Understand data persistence

**Task:** Keep track of what was downloaded

**Steps:**
1. Create a simple text file or JSON file
2. Write to it after each download:
```python
import json
history = {
    'timestamp': time.time(),
    'links': links,
    'files_downloaded': len(all_files)
}
with open('download_history.json', 'a') as f:
    f.write(json.dumps(history) + '\n')
```

**What you'll learn:** File I/O, JSON, data persistence

---

### Exercise 12: Parallel Downloads
**Goal:** Understand threading and concurrency

**Task:** Download multiple links at the same time

**Where:** `app.py`, in the download loop

**Change:**
```python
import threading

def download_with_thread(url):
    success, error = download_audio(url, session_dir)
    return (url, success, error)

threads = []
for url in links:
    thread = threading.Thread(target=download_with_thread, args=(url,))
    thread.start()
    threads.append(thread)

# Wait for all to complete
for thread in threads:
    thread.join()
```

**What you'll learn:** Threading, parallel processing, synchronization

---

## 🔴 Expert Exercises

### Exercise 13: Add User Authentication
**Goal:** Understand security and sessions

**Task:** Add simple password protection

**Steps:**
1. Install Flask-Login: `pip install flask-login`
2. Add login route
3. Protect download route with `@login_required`

**What you'll learn:** Authentication, sessions, security basics

---

### Exercise 14: Add Database
**Goal:** Understand databases and data modeling

**Task:** Store download history in SQLite database

**Steps:**
1. Install SQLite (comes with Python)
2. Create database schema
3. Store each download with metadata

**What you'll learn:** Databases, SQL, data modeling

---

### Exercise 15: Real-Time Updates with WebSockets
**Goal:** Understand real-time communication

**Task:** Show download progress in real-time

**Steps:**
1. Install Flask-SocketIO
2. Emit progress updates from Flask
3. Listen for updates in JavaScript

**What you'll learn:** WebSockets, real-time communication, event-driven architecture

---

## 🎯 Challenge Projects

### Challenge 1: Add Video Download Option
Create a toggle to choose between audio and video downloads.

**Hints:**
- Add radio buttons in HTML
- Pass choice to Flask
- Modify yt-dlp command based on choice

---

### Challenge 2: Create Download Queue
Allow users to queue up downloads and process them one at a time.

**Hints:**
- Store queue in memory or database
- Process queue in background thread
- Show queue status to user

---

### Challenge 3: Add Playlist Support
Detect if URL is a playlist and download all videos.

**Hints:**
- yt-dlp has playlist support built-in
- Use `--yes-playlist` flag
- Handle multiple files from one URL

---

## 📚 Study Questions

After doing exercises, answer these to test understanding:

1. **What happens when you click "Download All"?**
   - Trace the flow from button click to file download

2. **Why do we use `async/await` in JavaScript?**
   - What would happen without it?

3. **How does Flask know which function to run for each URL?**
   - Explain the routing system

4. **What's the difference between `request.form` and `request.json`?**
   - When would you use each?

5. **Why do we create temporary directories?**
   - What problems would occur without them?

6. **How does error handling work in both frontend and backend?**
   - Compare try/except vs try/catch

7. **What is the purpose of `subprocess.run()`?**
   - Why can't we just import yt-dlp as a Python library?

8. **Explain the difference between GET and POST requests.**
   - When would you use each?

---

## 🐛 Debugging Practice

### Scenario 1: Downloads Never Complete
**Symptoms:** Button says "Downloading..." forever

**Debugging steps:**
1. Check Flask console for errors
2. Verify yt-dlp is installed: `yt-dlp --version`
3. Test yt-dlp manually in terminal
4. Check network tab in browser (F12)
5. Add more `print()` statements in Flask

---

### Scenario 2: ZIP File is Empty
**Symptoms:** Download works but ZIP has no files

**Debugging steps:**
1. Check if files are actually downloaded (look in downloads folder)
2. Verify file paths are correct
3. Check file permissions
4. Add logging to see what files are found

---

### Scenario 3: "yt-dlp not found" Error
**Symptoms:** Server error about yt-dlp

**Debugging steps:**
1. Check if yt-dlp is in PATH: `where yt-dlp` (Windows) or `which yt-dlp` (Mac/Linux)
2. Try using full path to yt-dlp
3. Verify installation: `pip show yt-dlp`
4. Try reinstalling: `pip install --upgrade yt-dlp`

---

## 💡 Tips for Learning

1. **Start Small:** Modify one thing at a time
2. **Use Console:** Always check browser console (F12) and Flask console
3. **Read Errors:** Error messages tell you exactly what's wrong
4. **Experiment:** Break things on purpose to see what happens
5. **Google:** When stuck, search for the error message
6. **Documentation:** Read Flask and JavaScript docs
7. **Ask Questions:** "Why does this work?" is a great question

---

## 🎓 Next Learning Steps

After mastering these exercises:

1. **Learn about REST APIs:** How to structure API endpoints
2. **Study HTTP in depth:** Status codes, headers, methods
3. **Learn about deployment:** How to put this on AWS
4. **Study security:** Authentication, validation, sanitization
5. **Learn about testing:** Unit tests, integration tests
6. **Study databases:** SQL, ORMs, data modeling
7. **Learn about Docker:** Containerization for deployment

---

Remember: **The best way to learn is by doing!** Don't just read - modify the code, break it, fix it, and understand why it works.

