import streamlit as st
import requests
import json
import time
import logging

# Set page config
st.set_page_config(
    page_title="💼 AI Finance Coach",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .expense-progress {
        padding: 10px;
        background: #e3f2fd;
        border-radius: 8px;
        margin: 10px 0;
    }
    .advice-card {
        padding: 15px;
        background: #f5f5f5;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize session state
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

# Expense categories
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

# Configure sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("OpenRouter API Key", type="password")
    st.markdown("[Get API Key](https://openrouter.ai/keys)")

# Main interface
st.title("💼 Monthly Expense Analyzer")
st.caption("Get personalized financial advice based on your spending patterns")

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle expense collection
def handle_expense_collection(prompt: str):
    current_category = EXPENSE_CATEGORIES[st.session_state.current_category_index]
    
    # Validate numeric input
    try:
        amount = float(prompt.replace("$", "").replace(",", ""))
        st.session_state.expenses[current_category] = amount
        
        # Move to next category
        st.session_state.current_category_index += 1
        
        # Check if all categories collected
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

# Analyze collected expenses
def analyze_expenses():
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Format expenses for AI
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
            
            # Format analysis
            analysis = analysis.replace("**", "").replace("*", "•")
            
            # Stream response
            for line in analysis.split('\n'):
                full_response += line + "\n"
                response_placeholder.markdown(f"```{full_response}```")
                time.sleep(0.05)
                
            response_placeholder.markdown(full_response)
            
        except Exception as e:
            response_placeholder.error(f"Analysis error: {str(e)}")

# Chat input
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

# Show progress if collecting expenses
if st.session_state.collecting_expenses:
    progress = st.session_state.current_category_index / len(EXPENSE_CATEGORIES)
    current_category = EXPENSE_CATEGORIES[st.session_state.current_category_index]
    
    st.markdown(f"""
    <div class="expense-progress">
        📊 Collection Progress: {st.session_state.current_category_index}/{len(EXPENSE_CATEGORIES)} categories
        <br>
        Current Category: {current_category}
    </div>
    """, unsafe_allow_html=True)