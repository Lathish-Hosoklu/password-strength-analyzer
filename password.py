from flask import Flask, render_template_string, request, send_file
from zxcvbn import zxcvbn
import io
import itertools
import datetime

app = Flask(__name__)

LEET_MAP = {
    'a': ['a', '@', '4'],
    'e': ['e', '3'],
    'i': ['i', '1', '!'],
    'o': ['o', '0'],
    's': ['s', '$', '5'],
    't': ['t', '7'],
    'l': ['l', '1'],
}

def leetspeak_variants(word):
    substitutions = [LEET_MAP.get(c, [c]) for c in word.lower()]
    return set(''.join(combo) for combo in itertools.product(*substitutions))

def append_years(word, start_year=1990, end_year=None):
    end_year = end_year or (datetime.datetime.now().year + 2)
    return [f"{word}{year}" for year in range(start_year, end_year)]

def generate_wordlist(inputs):
    words = set()
    base_words = [w for w in inputs if w]
    for w in base_words:
        words.update(leetspeak_variants(w))
        words.update(leetspeak_variants(w[::-1]))
    for perm in itertools.permutations(base_words):
        merged = ''.join(perm)
        words.update(leetspeak_variants(merged))
    extended = set()
    for word in words:
        extended.update(append_years(word))
    return sorted(words | extended)

TEMPLATE = '''
<!doctype html>
<title>Password Analyzer & Wordlist Generator</title>
<h2>Password Strength Analyzer</h2>
<form method=post>
  Password: <input type="password" name="password">
  <input type="submit" name="analyze" value="Analyze">
</form>
{% if password_analysis %}
  <b>Score:</b> {{ password_analysis['score'] }}/4 <br>
  <b>Entropy:</b> {{ "{:.2f}".format(password_analysis['entropy']) }} <br>
  <b>Feedback:</b> {{ password_analysis['feedback'] or "None" }} <br>
{% endif %}
<hr>
<h2>Custom Wordlist Generator</h2>
<form method=post>
  Name: <input type="text" name="name"><br>
  Date (yyyy/mm/dd): <input type="text" name="date"><br>
  Pet Name: <input type="text" name="pet"><br>
  <input type="submit" name="generate" value="Generate">
</form>
{% if wordlist %}
  <b>Generated Wordlist ({{ word_count }} words):</b><br>
  <textarea rows=10 cols=50 readonly>{{ wordlist }}</textarea><br>
  <form method="post">
    <input type="hidden" name="name" value="{{ name }}">
    <input type="hidden" name="date" value="{{ date }}">
    <input type="hidden" name="pet" value="{{ pet }}">
    <input type="submit" name="download" value="Download .txt">
  </form>
{% endif %}
'''

@app.route("/", methods=["GET", "POST"])
def index():
    password_analysis = None
    wordlist = None
    name = date = pet = ""
    word_count = 0
    if request.method == "POST":
        if "analyze" in request.form and request.form.get("password"):
            result = zxcvbn(request.form.get("password"))
            password_analysis = {
                "score": result['score'],
                "entropy": result['entropy'],
                "feedback": " | ".join(result["feedback"]["suggestions"]) if result["feedback"]["suggestions"] else "None"
            }
        elif "generate" in request.form:
            name = request.form.get("name", "")
            date = request.form.get("date", "")
            pet = request.form.get("pet", "")
            wl = generate_wordlist([name, date, pet])
            wordlist = "\n".join(wl)
            word_count = len(wl)
        elif "download" in request.form:
            wl = generate_wordlist([request.form.get("name", ""), request.form.get("date", ""), request.form.get("pet", "")])
            wordlist_txt = "\n".join(wl)
            return send_file(
                io.BytesIO(wordlist_txt.encode()),
                mimetype="text/plain",
                as_attachment=True,
                attachment_filename="wordlist.txt"
            )
    return render_template_string(TEMPLATE, password_analysis=password_analysis, wordlist=wordlist,
                                 name=name, date=date, pet=pet, word_count=word_count)

if __name__ == "__main__":
    app.run(debug=True)
