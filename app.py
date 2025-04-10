import streamlit as st
import requests
import json
import time
import logging

st.set_page_config(
    page_title="💼 AI Finance Coach",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #2dba68;
        --background: #0f1114;
    }
    
    body {
        background-image: linear-gradient(rgba(11, 13, 16, 0.9), rgba(11, 13, 16, 0.9)),
                          url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1920');
        background-size: cover;
        background-attachment: fixed;
        color: #ffffff !important;
    }
    
    .stChatMessage {
        background: rgba(25, 28, 32, 0.9) !important;
        border: 1px solid #2dba6840 !important;
        border-radius: 12px;
        backdrop-filter: blur(4px);
    }
    
    .expense-progress {
        background: rgba(25, 28, 32, 0.9) !important;
        border: 1px solid #2dba6840;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        color: var(--primary) !important;
        font-weight: bold;
    }
    
    .stTextInput>div>div>input {
        color: #ffffff !important;
        background: rgba(25, 28, 32, 0.9) !important;
    }
    
    .stButton>button {
        background: var(--primary) !important;
        color: #000000 !important;
        border-radius: 8px;
        font-weight: bold;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(45, 186, 104, 0.3);
    }
</style>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO)

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Welcome! I'm your AI Finance Coach 💼 Let's analyze your monthly expenses!"
    }]
    
if "expenses" not in st.session_state:
    st.session_state.expenses = {}
    
if "collecting_expenses" not in st.session_state:
    st.session_state.collecting_expenses = False
    
if "current_category_index" not in st.session_state:
    st.session_state.current_category_index = 0

EXPENSE_CATEGORIES = [
    "🏠 Housing (rent/mortgage)",
    "🛒 Groceries",
    "🍔 Dining Out",
    "⛽ Transportation",
    "💡 Utilities",
    "💊 Healthcare",
    "🎉 Entertainment",
    "💳 Debt Payments",
    "📚 Education",
    "💰 Savings",
    "🎁 Miscellaneous"
]

with st.sidebar:
    st.title("⚙️ Settings")
    with st.container():
        api_key = st.text_input("OpenRouter API Key", type="password", help="Required for AI functionality")
        st.markdown("[Get API Key](https://openrouter.ai/keys)")
        
        with st.expander("📘 Quick Start Guide"):
            st.markdown("""
            1. Enter API key above
            2. Click 'Start' in chat
            3. Input expense amounts
            4. Get financial insights
            """)
        
        model_name = st.selectbox(
            "🤖 Analysis Model",
            ("google/palm-2-chat-bison",),
            index=0
        )
        
        with st.expander("⚡ Advanced Settings"):
            analysis_depth = st.slider("🔍 Analysis Depth", 0.0, 1.0, 0.7)
            max_retries = st.number_input("🔄 Max Retries", 1, 5, 2)
        
        st.markdown("### 🚀 Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Chat", use_container_width=True):
                st.session_state.messages = [{
                    "role": "assistant",
                    "content": "Chat cleared! Ready to analyze expenses!"
                }]
        with col2:
            if st.button("📋 Example Prompt", use_container_width=True):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Try typing 'start' to begin expense analysis!"
                })

st.title("💼 Monthly Expense Analyzer")
st.caption("Get personalized financial advice based on your spending patterns")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def handle_expense_collection(prompt: str):
    current_category = EXPENSE_CATEGORIES[st.session_state.current_category_index]
    
    try:
        amount = float(prompt.replace("$", "").replace(",", ""))
        st.session_state.expenses[current_category] = amount
        
        st.session_state.current_category_index += 1
        
        if st.session_state.current_category_index >= len(EXPENSE_CATEGORIES):
            st.session_state.collecting_expenses = False
            analyze_expenses()
        else:
            next_category = EXPENSE_CATEGORIES[st.session_state.current_category_index]
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Got it! Now please enter your monthly amount for:\n**{next_category}**"
            })
            
    except ValueError:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Please enter a valid number for {current_category}"
        })

def analyze_expenses():
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            expenses_str = "\n".join(
                [f"{category}: ${amount}" 
                 for category, amount in st.session_state.expenses.items()]
            )
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/palm-2-chat-bison",
                    "messages": [{
                        "role": "system",
                        "content": f"""Act as a financial advisor. Analyze these monthly expenses:
                        
                        {expenses_str}
                        
                        Provide:
                        1. Spending pattern summary
                        2. 3 cost-cutting recommendations
                        3. Savings optimization tips
                        4. Debt management strategies
                        5. Emergency fund advice
                        
                        Use simple language with emojis and bullet points. Avoid markdown."""
                    }]
                }
            )
            
            response.raise_for_status()
            analysis = response.json()['choices'][0]['message']['content']
            
            analysis = analysis.replace("**", "").replace("*", "•")
            
            for line in analysis.split('\n'):
                full_response += line + "\n"
                response_placeholder.markdown(full_response)
                time.sleep(0.05)
                
        except Exception as e:
            response_placeholder.error(f"Analysis error: {str(e)}")

if prompt := st.chat_input("Type 'start' to begin expense analysis..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        with st.chat_message("assistant"):
            st.error("🔑 API key required in sidebar")
        st.stop()

    if prompt.lower() == 'start':
        st.session_state.collecting_expenses = True
        st.session_state.current_category_index = 0
        st.session_state.expenses = {}
        first_category = EXPENSE_CATEGORIES[0]
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Let's analyze your expenses! Please enter your monthly amount for:\n**{first_category}**"
        })
    elif st.session_state.collecting_expenses:
        handle_expense_collection(prompt)
    else:
        with st.chat_message("assistant"):
            st.info("Type 'start' to begin expense analysis")

if st.session_state.collecting_expenses:
    progress = st.session_state.current_category_index / len(EXPENSE_CATEGORIES)
    current_category = EXPENSE_CATEGORIES[st.session_state.current_category_index]
    
    st.markdown(f"""
    <div class="expense-progress">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>📊 Collection Progress</span>
            <span>{st.session_state.current_category_index}/{len(EXPENSE_CATEGORIES)}</span>
        </div>
        <div style="height: 6px; background: #2dba6820; border-radius: 3px;">
            <div style="width: {progress*100}%; height: 100%; 
                     background: var(--primary); border-radius: 3px; 
                     transition: width 0.3s ease;">
            </div>
        </div>
        <div style="margin-top: 12px; color: #ffffffb0;">
            Current Category: {current_category}
        </div>
    </div>
    """, unsafe_allow_html=True)