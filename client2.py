import streamlit as st
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
import json
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()
load_dotenv()

# Server configuration
SERVERS = {
    "math": {
        "transport": "stdio",
        "command": "C:\\Users\\PC\\.local\\bin\\uv.exe",
        "args": [
            "run",
            "fastmcp",
            "run",
            "D:\\FastMCP-Server\\main_01.py"
        ]
    },
    "expense": {
        "transport": "streamable_http",
        "url": "https://lakhan-expense-tracker.fastmcp.app/mcp"
    }
}

# Page config
st.set_page_config(
    page_title="Expense Tracker AI Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 10px;
    }
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sidebar-content {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stButton > button {
        background-color: rgba(102, 126, 234, 0.8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: rgba(118, 75, 162, 0.9);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = None
if "tools" not in st.session_state:
    st.session_state.tools = None
if "named_tools" not in st.session_state:
    st.session_state.named_tools = {}


def get_or_create_eventloop():
    """Get or create event loop"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


async def initialize_mcp_client():
    """Initialize MCP client and tools"""
    if st.session_state.mcp_client is None:
        client = MultiServerMCPClient(SERVERS)
        tools = await client.get_tools()
        
        named_tools = {}
        for tool in tools:
            named_tools[tool.name] = tool
        
        st.session_state.mcp_client = client
        st.session_state.tools = tools
        st.session_state.named_tools = named_tools
        st.session_state.initialized = True
        
        return client, tools, named_tools
    return st.session_state.mcp_client, st.session_state.tools, st.session_state.named_tools


async def process_message(prompt: str):
    """Process user message and get AI response"""
    client, tools, named_tools = await initialize_mcp_client()
    
    llm = ChatOpenAI(model="gpt-4")
    llm_with_tools = llm.bind_tools(tools)
    
    # Get initial response
    response = await llm_with_tools.ainvoke(prompt)
    
    # Check if tools were called
    if not getattr(response, "tool_calls", None):
        return response.content, None
    
    # Process tool calls
    tool_messages = []
    tool_results = []
    
    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]
        
        result = await named_tools[selected_tool].ainvoke(selected_tool_args)
        tool_messages.append(
            ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result))
        )
        tool_results.append({
            "tool": selected_tool,
            "args": selected_tool_args,
            "result": result
        })
    
    # Get final response
    final_response = await llm_with_tools.ainvoke([prompt, response, *tool_messages])
    
    return final_response.content, tool_results


# Header
st.markdown("""
    <div class="chat-header">
        <h1>💰 Expense Tracker AI Assistant</h1>
        <p>Your intelligent financial companion</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View Expenses", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "Show me my recent expenses"
            })
            st.rerun()
    
    with col2:
        if st.button("➕ Add Expense", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "Help me add a new expense"
            })
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 💡 Example Questions")
    examples = [
        "What are my expenses for this month?",
        "Show me my spending by category",
        "What's my total spending this week?",
        "Add a $50 grocery expense",
        "Calculate my average daily spending"
    ]
    
    for example in examples:
        if st.button(example, key=example, use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": example
            })
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
        This AI assistant helps you:
        - 📊 Track expenses
        - 📈 Analyze spending patterns
        - 💡 Get financial insights
        - 🧮 Perform calculations
    """)
    
    # Connection status
    st.markdown("---")
    if st.session_state.initialized:
        st.success("✅ Connected to MCP servers")
        st.info(f"🔧 {len(st.session_state.named_tools)} tools available")
    else:
        st.info("⏳ Waiting for first query...")

# Chat container
chat_container = st.container()

# Display chat history
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show tool results if available
            if "tool_results" in message and message["tool_results"]:
                with st.expander("🔧 Tool Executions"):
                    for tool_result in message["tool_results"]:
                        st.json(tool_result)

# Chat input
if prompt := st.chat_input("Ask me anything about your expenses..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                loop = get_or_create_eventloop()
                response_content, tool_results = loop.run_until_complete(process_message(prompt))
                
                st.markdown(response_content)
                
                # Show tool results if available
                if tool_results:
                    with st.expander("🔧 Tool Executions"):
                        for tool_result in tool_results:
                            st.json(tool_result)
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content,
                    "tool_results": tool_results
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                
                # Show detailed error in expander
                with st.expander("🔍 Error Details"):
                    st.code(str(e))