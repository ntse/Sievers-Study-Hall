# Security Issues - Quick Fix Guide

## 🔴 CRITICAL (Fix Immediately)

### 1. Hardcoded Secret Key
**File:** `app.py:14`

**Current:**
```python
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'secret_key_for_development_environment')
```

**Fix:**
```python
secret_key = os.environ.get('FLASK_SECRET_KEY')
if not secret_key:
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("FLASK_SECRET_KEY must be set in production")
    secret_key = 'dev-only-secret-key'
app.secret_key = secret_key
```

---

### 2. Add Security Headers
**File:** `app.py` (add after all configuration)

**Add:**
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

### 3. Session Security Hardening
**File:** `app.py:38-39`

**Current:**
```python
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
```

**Fix:**
```python
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Reduced from 30 days
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PREFERRED_URL_SCHEME'] = 'https'
```

---

### 4. Input Validation for User Answers
**File:** `webapp/routes/exercises.py` (add new function at top)

**Add:**
```python
def validate_and_sanitize_answer(answer, max_length=10000):
    """Validate and sanitize user-submitted exercise answers."""
    if not isinstance(answer, str):
        abort(400, "Invalid answer format")
    if len(answer) > max_length:
        abort(413, f"Answer exceeds maximum length of {max_length} characters")
    # Remove null bytes that could cause issues
    answer = answer.replace('\x00', '')
    return answer.strip()
```

**Then fix line ~226:**
```python
# OLD:
user_answer = request.form.get('answer', '')

# NEW:
user_answer = validate_and_sanitize_answer(request.form.get('answer', ''))
```

---

### 5. Secure AI API Integration
**File:** `users/questions/prompting.py` (modify make_request function)

**Add error handling that doesn't log tokens:**
```python
def make_request(temperature):
    try:
        response = client.chat.completions.create(
            model=model[level],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1000,
            response_format=response_format,
            extra_body={"reasoning_effort": "low"}
        )
        # ... rest of code
    except Exception as e:
        # NEVER log the full exception (may contain API key)
        logger.error(f"AI API error: {type(e).__name__}", exc_info=False)
        raise

# Add at top of file:
import logging
logger = logging.getLogger(__name__)
```

---

### 6. Fix Textarea XSS
**File:** `webapp/templates/exercise/feedback.html:38,44`

**Add markupsafe escaping in route first:**

In `webapp/routes/exercises.py` add imports:
```python
from markupsafe import escape
```

Then escape before passing to template (in `feedback_page` function around line 310):
```python
user_answer_safe = escape(user_answer)
```

**Update template variable:**
```html
<!-- Line 38: OLD -->
<input type="text" class="readonly-input" value="{{ user_answer }}" readonly>

<!-- NEW -->
<input type="text" class="readonly-input" value="{{ user_answer_safe }}" readonly>

<!-- Line 44: OLD -->
<textarea class="readonly-prompt" readonly>{{ user_answer }}</textarea>

<!-- NEW -->
<textarea class="readonly-prompt" readonly>{{ user_answer_safe }}</textarea>
```

---

## 🟡 HIGH PRIORITY (Fix This Week)

### 7. Prompt Injection Prevention
**File:** `users/questions/prompting.py:62`

**Add sanitization:**
```python
def sanitize_for_prompt(text):
    """Sanitize text to prevent prompt injection."""
    # Quote the text as JSON to safely embed in prompt
    return json.dumps(text, ensure_ascii=False)

# Update format_prompt call:
# OLD: prompt = format_prompt(unit, exercise, language, question_id, user_answer)
# NEW:
sanitized_answer = sanitize_for_prompt(user_answer)
prompt = f"User submitted answer: {sanitized_answer}\n\n[rest of prompt]"
```

---

### 8. Database Query Optimization
**File:** `users/progress/progress.py` and similar files

**Example fix for N+1 queries:**

**OLD:**
```python
rows = UserExerciseState.query.filter_by(user_id=user_id).all()
for row in rows:
    result = UserExerciseState.query.filter_by(...).first()  # Query per iteration!
```

**NEW:**
```python
# Load everything in one query with eager loading
rows = UserExerciseState.query.filter_by(user_id=user_id).all()
# Create dict for O(1) lookup instead of querying again
result_map = {row.id: row for row in rows}
```

---

### 9. Session Cleanup Performance
**File:** `webapp/routes/background.py:62` - Remove expensive after_request handler

**Current (SLOW):**
```python
@routes_bp.after_request
def clear_empty_unit_dictionary(response):
    if session_size(session) > 3000:
        for unit in units:
            for exercise in range(100):
                # Runs on EVERY request
```

**Better approach - Run only when needed:**
```python
# Keep the function but add guards
@routes_bp.after_request
def clear_empty_unit_dictionary(response):
    # Only run on specific routes that modify session
    if request.endpoint not in ['routes.check_answer', 'routes.set_feedback']:
        return response
    
    if session_size(session) > 3000:
        # Existing cleanup logic, but only when actually needed
        # ...
    return response
```

---

### 10. Privacy Policy TODO Items
**File:** `webapp/templates/menu/privacy_en.html`

**Replace all TODO comments with actual information:**

**Line 20 - Add data controller details:**
```html
<!-- OLD -->
<!-- TODO: Identify the data controller (name and, where legally required, postal contact details). -->

<!-- NEW -->
<p><strong>Data Controller:</strong> [Your Name/Organization]<br>
Contact: sieversstudyhall@gmail.com</p>
```

**Line 50 - Add AI provider details:**
```html
<!-- OLD -->
<!-- TODO: Name the actual AI provider(s), routing intermediaries, processing locations, retention and training policies; verify whether account identifiers are sent. -->

<!-- NEW -->
<p><strong>AI Service Provider:</strong> Groq (via Hugging Face API)<br>
<strong>Processing Location:</strong> [Check Groq's data centers]<br>
<strong>Data Retention:</strong> [Confirm with Groq]<br>
<strong>Training Use:</strong> User submissions may be used for model improvement unless opted out<br>
<strong>User Identifiers Sent:</strong> Only exercise context, not account information</p>
```

---

## 📋 Validation Checklist

After implementing fixes, verify:

```bash
# 1. Check secret key configuration
grep -n "FLASK_SECRET_KEY" app.py

# 2. Verify security headers are present
curl -I https://yourapp.com | grep -E "X-|Content-Security"

# 3. Test input validation (should reject long inputs)
curl -X POST https://yourapp.com/check/unit/exercise/1 \
  -d "answer=$(python3 -c 'print("A"*20000)')"

# 4. Verify session cookie flags
curl -I https://yourapp.com | grep -i "set-cookie"
# Should show: Secure; HttpOnly; SameSite=Lax

# 5. Check for null bytes in handling
python3 -c "
import requests
r = requests.post('http://localhost:5000/check/unit1/exercise/1', 
                  data={'answer': 'test\x00injection'})
print('Status:', r.status_code)
"
```

---

## 🔐 Deployment Checklist

Before production deployment:

- [ ] Set `FLASK_SECRET_KEY` environment variable (minimum 32 characters, random)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set `FLASK_ENV=production`
- [ ] Verify all security headers are present
- [ ] Configure `HF_TOKEN` without exposing in logs
- [ ] Set up database backups
- [ ] Enable request logging and monitoring
- [ ] Review privacy policy with legal team
- [ ] Test session timeout works (don't stay logged in after 24h)
- [ ] Verify CORS is restricted if needed
- [ ] Load test to identify N+1 query bottlenecks

---

## Testing Commands

```bash
# Test secret key fallback
python3 -c "import app; print('OK' if app.app.secret_key != 'secret_key_for_development_environment' else 'FAIL')"

# Test security headers
curl -s -I http://localhost:5000 | grep -c "X-Content-Type-Options"

# Test input validation
python3 -c "
from webapp.routes.exercises import validate_and_sanitize_answer
try:
    validate_and_sanitize_answer('A' * 20000)
except:
    print('Input validation works')
"
```

---

**Priority Order for Fixes:**
1. Secret key (5 min)
2. Security headers (10 min)
3. Session config (5 min)
4. Input validation (15 min)
5. AI API error handling (10 min)
6. Textarea escaping (10 min)
7. Prompt injection fix (15 min)
8. Database optimization (varies)
9. Session cleanup optimization (20 min)
10. Privacy policy completion (30 min)

**Estimated Total Time:** ~2.5 hours for all fixes
