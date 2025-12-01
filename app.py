import streamlit as st
import google.generativeai as genai
import json
import textwrap

# Page config
st.set_page_config(page_title="AI Exam Revision Tool", layout="wide", page_icon="🚀")

# Custom CSS for beauty
st.markdown("""
<style>
.main {background-color: #f0f8ff}
.stButton > button {border-radius: 20px; font-weight: bold}
.stTextInput > div > div > input {border-radius: 10px}
.metric {background-color: #4CAF50; color: white; border-radius: 10px}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI Exam Revision & Self-Evaluation Tool")
st.markdown("*Generate custom quizzes + Get AI-powered feedback instantly!*")

# Sidebar for API key
with st.sidebar:
    st.header("🔑 Setup")
    api_key = st.text_input("Gemini API Key", type="password", 
                           help="Get from aistudio.google.com")
    st.info("💡 Free tier: 1000 requests/day")

# Initialize session state
if "questions" not in st.session_state:
    st.session_state.questions = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}

# Configure API
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

# Main interface
col1, col2 = st.columns([2,1])

with col1:
    st.header("📚 Create Your Quiz")
    subject = st.text_input("Subject", placeholder="e.g., Science, Maths, History")
    topic = st.text_input("Topic", placeholder="e.g., Photosynthesis, Algebra")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=0)
    num_questions = st.slider("Number of Questions", 3, 10, 5)
    
    if st.button("🎯 Generate Quiz!", type="primary", use_container_width=True):
        if subject and topic and api_key:
            with st.spinner("🤖 AI generating questions..."):
                st.session_state.questions = generate_questions(subject, topic, difficulty, num_questions, model)
                st.session_state.answers = {}
                st.rerun()
        else:
            st.error("Please fill subject, topic & API key!")

# Quiz Section
if st.session_state.questions:
    st.header("📝 Take the Quiz")
    
    # Progress bar
    progress = len([a for a in st.session_state.answers.values() if a]) / len(st.session_state.questions)
    st.progress(progress)
    
    # Questions
    for i, q in enumerate(st.session_state.questions):
        with st.expander(f"Q{i+1}: {q['question'][:60]}..."):
            st.write(q['question'])
            colA, colB, colC, colD = st.columns(4)
            with colA:
                st.session_state.answers[str(i)] = st.radio(
                    f"Q{i+1}", ["A", "B", "C", "D"], 
                    key=f"q{i}", index=list(st.session_state.answers.get(str(i), "A"))
                )
    
    # Submit button
    if st.button("📊 Submit & Get AI Feedback!", type="secondary"):
        st.session_state.score = calculate_score(st.session_state.questions, st.session_state.answers)
        st.rerun()

# Results Section
if st.session_state.score > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Score", f"{st.session_state.score}/{len(st.session_state.questions)}")
    with col2:
        st.metric("Percentage", f"{st.session_state.score/len(st.session_state.questions)*100:.0f}%")
    with col3:
        rating = "🏆 Excellent!" if st.session_state.score == len(st.session_state.questions) else "👍 Good!" if st.session_state.score >= len(st.session_state.questions)//2 else "📚 Keep Practicing!"
        st.metric("Rating", rating)
    
    # Detailed results
    st.header("📋 Detailed Results")
    for i, q in enumerate(st.session_state.questions):
        ans = st.session_state.answers.get(str(i), "")
        correct = q['correct']
        color = "green" if ans == correct else "red"
        st.markdown(f"*Q{i+1}:* {q['question']}")
        st.markdown(f"*Your answer:* <span style='color:{color}'>{ans}</span> | *Correct:* {correct}", unsafe_allow_html=True)
        if ans != correct:
            st.info(f"💡 *Explanation:* {q['explanation']}")
        st.markdown("---")
    
    # AI Feedback
    if st.button("🤖 Generate AI Study Plan"):
        with st.spinner("AI analyzing your performance..."):
            feedback = generate_feedback(st.session_state.questions, st.session_state.answers, subject, topic)
            st.markdown("### 🎯 *Your Personalized Study Plan*")
            st.markdown(feedback)

# Helper functions (same as before but adapted)
@st.cache_data
def generate_questions(subject, topic, difficulty, num_questions, model):
    prompt = f"""Create exactly {num_questions} MCQs for {subject} "{topic}" ({difficulty}).
Output ONLY valid JSON array with question, options["A)..."], correct, explanation."""
    
    raw = model.generate_content(prompt).text
    raw = raw.replace("``````", "").replace("$", "").strip()
    
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end > start:
        raw = raw[start:end+1]
    
    try:
        data = json.loads(raw)
        return data[:num_questions]
    except:
        return [{"question": f"What is {topic}?", "options": ["A) Yes", "B) No", "C) Maybe", "D) IDK"], "correct": "A", "explanation": "Learn basics!"}]

def calculate_score(questions, answers):
    score = 0
    for i, q in enumerate(questions):
        if answers.get(str(i), "") == q['correct']:
            score += 1
    return score

def generate_feedback(questions, answers, subject, topic):
    mistakes = [i for i, q in enumerate(questions) if answers.get(str(i), "") != q['correct']]
    return f"""*Great job on {subject}!* 🎉

*Strengths:* You got {len(questions)-len(mistakes)}/{len(questions)} correct!

*Focus Areas ({len(mistakes)} mistakes):*
• Review {topic} basics
• Practice similar questions

*3 Quick Tips:*
1. Make flashcards for key terms
2. Explain concepts to someone else
3. Do 5 more practice questions daily

*Next Practice:*
• What are the main parts of {topic}?
• Why is {topic} important in {subject}?"""

else:
    st.markdown("""
    ## ✨ *How to use:*
    1. Get FREE API key: [aistudio.google.com](https://aistudio.google.com)
    2. Enter subject & topic 
    3. Generate quiz → Answer → Get AI feedback!
    
    *Perfect for school projects!* 📚
    """)
