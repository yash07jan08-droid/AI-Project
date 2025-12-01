import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="AI Exam Revision Tool", page_icon="🚀")

st.title("🚀 AI Exam Revision & Self‑Evaluation Tool")
st.write("Enter your Gemini API key, subject and topic, then get a quiz and feedback.")

# --- API KEY ---
api_key = st.sidebar.text_input("Gemini API key", type="password")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

# --- INPUTS ---
subject = st.text_input("Subject", "Maths")
topic = st.text_input("Topic", "Algebra")
difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=0)
num_questions = st.slider("Number of questions", 3, 10, 5)

# placeholders in session
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "score" not in st.session_state:
    st.session_state.score = None
if "feedback" not in st.session_state:
    st.session_state.feedback = ""

# --- FUNCTIONS ---
def generate_questions():
    prompt = f"""Create exactly {num_questions} multiple‑choice questions for {subject} on "{topic}" ({difficulty} level).

Output ONLY valid JSON like:
[
  {{"question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"correct":"A","explanation":"..."}},
  ...
]"""

    resp = model.generate_content(prompt).text
    resp = resp.replace("``````", "").replace("$", "").strip()
    start = resp.find("[")
    end = resp.rfind("]")
    if start != -1 and end > start:
        resp = resp[start:end+1]

    try:
        data = json.loads(resp)
        return data[:num_questions]
    except Exception:
        return [{
            "question": f"What is {topic} in {subject}?",
            "options": ["A) Basic idea", "B) Hard theorem", "C) History", "D) Formula"],
            "correct": "A",
            "explanation": "Know the basic idea first."
        }] * num_questions

def calc_score():
    score = 0
    for i, q in enumerate(st.session_state.questions):
        if st.session_state.answers.get(i) == q["correct"]:
            score += 1
    return score

def make_feedback():
    mistakes = []
    for i, q in enumerate(st.session_state.questions):
        ans = st.session_state.answers.get(i)
        if ans != q["correct"]:
            mistakes.append(f"Q: {q['question']} | Your: {ans} | Correct: {q['correct']}")
    mistakes_text = "\n".join(mistakes) if mistakes else "No mistakes."

    prompt = f"""You are a friendly school tutor.

Subject: {subject}
Topic: {topic}
Score: {st.session_state.score}/{len(st.session_state.questions)}

Mistakes:
{mistakes_text}

Give:
1) 1 sentence of encouragement
2) 2–3 sentences on weak areas
3) 3 short, practical study tips.
Keep it short and simple."""
    return model.generate_content(prompt).text

# --- UI LOGIC ---
if st.button("Generate quiz"):
    if not api_key:
        st.error("Enter your API key in the sidebar.")
    else:
        st.session_state.questions = generate_questions()
        st.session_state.answers = {}
        st.session_state.score = None
        st.session_state.feedback = ""

if st.session_state.questions:
    st.subheader("Quiz")
for i, q in enumerate(st.session_state.questions):
    st.write(f"*Q{i+1}. {q['question']}*")

    # Build label with option letters + text
    options = q.get("options", [])
    labeled_options = []
    letters = ["A", "B", "C", "D"]
    for idx, opt in enumerate(options):
        letter = letters[idx]
        # if opt already starts with "A) ..." keep as is, else add
        if opt.strip().upper().startswith(tuple([f"{l})" for l in letters])):
            labeled_options.append(opt)
        else:
            labeled_options.append(f"{letter}) {opt}")

    choice = st.radio(
        f"Your answer for Q{i+1}",
        labeled_options,
        key=f"q{i}"
    )

    # Store only the letter (A/B/C/D)
    st.session_state.answers[i] = choice[0] if choice else ""
   st.write("")

    if st.button("Submit answers"):
        st.session_state.score = calc_score()
        st.session_state.feedback = make_feedback()

if st.session_state.score is not None:
    st.subheader("Results")
    st.write(f"Score: {st.session_state.score} / {len(st.session_state.questions)}")
    st.markdown("### AI Feedback")
    st.write(st.session_state.feedback)
