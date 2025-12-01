import streamlit as st
import google.generativeai as genai
import json

# ---------------- BASIC SETUP ----------------

st.set_page_config(page_title="AI Exam Revision Tool", page_icon="🚀")

st.title("🚀 AI Exam Revision & Self‑Evaluation Tool")
st.write("Generate custom quizzes using AI, answer them, and see detailed feedback.")

# --- API KEY (sidebar) ---
api_key = st.sidebar.text_input("Gemini API key", type="password", help="Get it from aistudio.google.com")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# --- USER INPUTS ---
subject = st.text_input("Subject", "Maths")
topic = st.text_input("Topic", "Algebra")
difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=0)
num_questions = st.slider("Number of questions", 3, 10, 5)

# --- SESSION STATE ---
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "score" not in st.session_state:
    st.session_state.score = None

# ---------------- FUNCTIONS ----------------

def generate_questions():
    prompt = f"""Create exactly {num_questions} multiple-choice questions for {subject} on "{topic}" ({difficulty} level).

Each question must have:
- EXACTLY 4 options: A), B), C), D)
- 'correct' as the correct option letter (A/B/C/D)
- 'explanation' explaining why the correct answer is right in 1–2 sentences.

Return ONLY valid JSON like this:
[
  {{"question": "Question text", "options": ["Option A text", "Option B text", "Option C text", "Option D text"], "correct": "A", "explanation": "Reason here"}},
  ...
]
"""

    try:
        resp = model.generate_content(prompt)
        text = resp.text
    except Exception as e:
        st.error(f"Gemini API error while generating questions: {e}")
        return []

    # clean text
    text = text.replace("``````", "").replace("$", "").strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        text = text[start:end+1]

    try:
        data = json.loads(text)
        # ensure correct shape
        clean_questions = []
        for q in data[:num_questions]:
            question = q.get("question", "No question")
            options = q.get("options", [])
            correct = q.get("correct", "A").strip().upper()
            explanation = q.get("explanation", "")

            # pad / trim options to 4
            options = list(options)[:4]
            while len(options) < 4:
                options.append("Dummy option")

            clean_questions.append({
                "question": question,
                "options": options,
                "correct": correct,
                "explanation": explanation
            })
        return clean_questions
    except Exception:
        # simple fallback
        return [{
            "question": f"What is {topic} in {subject}?",
            "options": ["Basic idea", "Hard theorem", "History", "Formula"],
            "correct": "A",
            "explanation": "You should first know the basic idea."
        }] * num_questions

def calculate_score(questions, answers):
    score = 0
    for i, q in enumerate(questions):
        if answers.get(i) == q["correct"]:
            score += 1
    return score

# ---------------- UI LOGIC ----------------

# 1) Generate quiz
if st.button("Generate quiz"):
    if not api_key:
        st.error("Enter your Gemini API key in the sidebar.")
    elif not model:
        st.error("Model not initialized.")
    else:
        st.session_state.questions = generate_questions()
        st.session_state.answers = {}
        st.session_state.score = None

# 2) Show quiz
if st.session_state.questions:
    st.subheader("Quiz")

    letters = ["A", "B", "C", "D"]

    for i, q in enumerate(st.session_state.questions):
        st.markdown(f"*Q{i+1}. {q['question']}*")

        # build labeled options: "A) text"
        labeled_options = []
        for idx, opt_text in enumerate(q["options"]):
            if idx < 4:
                labeled_options.append(f"{letters[idx]}) {opt_text}")
        choice = st.radio(
            f"Your answer for Q{i+1}",
            labeled_options,
            key=f"q{i}"
        )

        # store just the letter (A/B/C/D)
        st.session_state.answers[i] = choice[0] if choice else ""

        st.write("")

    # 3) Submit answers
    if st.button("Submit answers"):
        st.session_state.score = calculate_score(st.session_state.questions, st.session_state.answers)

# 4) Results + explanations
if st.session_state.score is not None:
    qs = st.session_state.questions
    ans = st.session_state.answers

    st.subheader("Results")
    st.write(f"Score: {st.session_state.score} / {len(qs)}")

    st.markdown("### Question-wise feedback")

    for i, q in enumerate(qs):
        your = ans.get(i, "")
        correct = q["correct"]
        explanation = q.get("explanation", "")

        st.markdown(f"*Q{i+1}. {q['question']}*")

        if your == correct:
            st.success(f"✅ You chose {your}, which is correct.")
            if explanation:
                st.write(f"Reason: {explanation}")
        else:
            st.error(f"❌ Your answer: {your or 'No answer'} | Correct: {correct}")
            if explanation:
                st.write(f"Why the correct option is right: {explanation}")
                st.write("Why your option is wrong: It does not match the key idea explained above.")

        st.markdown("---")
