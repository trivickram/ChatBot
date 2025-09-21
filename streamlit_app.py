"""
Shim to prefer the pysqlite3 package over the system `sqlite3` module.
Some environments have an older system SQLite that causes runtime/version
conflicts with packages; this forces Python to use `pysqlite3` when available.

If `pysqlite3` is not installed, this will silently fall back to the bundled
`sqlite3` module so the app still runs.
"""
try:
    __import__('pysqlite3')
    import sys
    # Replace the stdlib sqlite3 module with pysqlite3 so imports of `sqlite3`
    # in third-party packages use the vendored newer build.
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    # pysqlite3 not available; continue using the system sqlite3 module.
    pass

import streamlit as st

# Page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="EmpowerHR - AI-Powered HR Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import smtplib
import ssl
from email.message import EmailMessage
from textwrap import dedent
from dotenv import load_dotenv
from datetime import datetime, timedelta
import tempfile
import json



# Load environment variables
load_dotenv()

# Helper: check LLM configuration (OpenAI or Google Gemini)
def check_llm_config():
    """Return (ok: bool, message: str, detected_keys: dict) about LLM API key configuration."""
    detected = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY')
    }

    if detected['OPENAI_API_KEY']:
        return True, "OpenAI key detected.", detected
    # If using Gemini, one of GEMINI_API_KEY or GOOGLE_API_KEY might be set
    if detected['GEMINI_API_KEY'] or detected['GOOGLE_API_KEY']:
        return True, "Google Gemini key detected.", detected

    # Nothing found
    user_msg = (
        "No LLM API keys were found.\n\n"
        "If you want to use OpenAI (GPT), set the environment variable `OPENAI_API_KEY`.\n"
        "If you want to use Google Gemini, set `GEMINI_API_KEY` or the provider-specific key and ensure crewai/litellm is configured for Google.\n\n"
        "After setting the key, restart this Streamlit app."
    )
    return False, user_msg, detected

# Import CrewAI components
try:
    from crewai import Crew, Agent, Task, Process
    from crewai_tools import DOCXSearchTool, CSVSearchTool, TXTSearchTool, SerperDevTool
    CREWAI_AVAILABLE = True
except ImportError:
    import sys, traceback
    CREWAI_AVAILABLE = False
    tb = traceback.format_exc()
    st.error("CrewAI not installed. Please install with: pip install crewai crewai-tools")
    # Diagnostic info to help the user identify which Python/paths Streamlit is using
    st.markdown("**Diagnostic information (helpful for fixing environment issues):**")
    st.code(f"Python executable: {sys.executable}\n\nsys.path:\n{chr(10).join(sys.path)}\n\nImportError traceback:\n{tb}")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
# Store generated email (subject/body/raw) so Send Email works across reruns
if 'generated_email' not in st.session_state:
    st.session_state.generated_email = None
if 'generated_subject' not in st.session_state:
    st.session_state.generated_subject = None
if 'generated_body' not in st.session_state:
    st.session_state.generated_body = None

def initialize_tools():
    """Initialize search tools for documents and data"""
    try:
        # Document search tool
        doc_search = DOCXSearchTool("docs/Employee-Code-of-Conduct.docx")
        
        # CSV search tool for interview data
        csv_search = CSVSearchTool('interview_data.csv')
        
        # Google search tool
        google_search = SerperDevTool()
        
        return doc_search, csv_search, google_search
    except Exception as e:
        st.error(f"Error initializing tools: {str(e)}")
        return None, None, None

def create_hr_agents():
    """Create HR specialized agents"""
    try:
        # Meeting Preparation Agent
        meeting_prep_agent = Agent(
            role="Meeting Preparation Specialist",
            goal="Prepare comprehensive meeting notes and analysis for HR discussions",
            backstory="""You are an experienced HR specialist who excels at preparing for meetings. 
            You analyze candidate information, company policies, and create structured meeting notes 
            that help HR professionals conduct effective interviews and discussions.""",
            verbose=True,
            allow_delegation=False
        )
        
        # FAQ Specialist Agent
        faq_agent = Agent(
            role="HR Policy Expert",
            goal="Provide accurate answers to HR policy questions based on company documentation",
            backstory="""You are an expert in HR policies and procedures. You have deep knowledge 
            of employee handbooks, code of conduct, and company policies. You provide clear, 
            accurate answers to employee questions.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Email Specialist Agent
        email_agent = Agent(
            role="Professional Communication Specialist",
            goal="Draft professional HR emails and communications",
            backstory="""You are a skilled professional communicator who specializes in HR 
            communications. You draft clear, professional, and appropriate emails for various 
            HR scenarios including offers, rejections, policy updates, and general communications.""",
            verbose=True,
            allow_delegation=False
        )
        
        return meeting_prep_agent, faq_agent, email_agent
    except Exception as e:
        st.error(f"Error creating agents: {str(e)}")
        return None, None, None

def create_meeting_notes(user_input):
    """Generate meeting preparation notes"""
    if not CREWAI_AVAILABLE:
        return "CrewAI is not available. Please install required dependencies."
    # Verify LLM configuration before attempting to call CrewAI
    ok, llm_msg, detected = check_llm_config()
    if not ok:
        masked = {k: ('SET' if v else None) for k, v in detected.items()}
        return f"LLM configuration error: {llm_msg}\n\nDetected keys (masked): {masked}"
    
    try:
        doc_search, csv_search, google_search = initialize_tools()
        meeting_agent, _, _ = create_hr_agents()
        
        if not all([doc_search, csv_search, google_search, meeting_agent]):
            return "Error initializing AI components."
        
        # Create task for meeting preparation
        meeting_task = Task(
            description=f"""
            Prepare comprehensive meeting notes based on this request: {user_input}
            
            Use the available tools to:
            1. Search relevant company policies and documents
            2. Look up any relevant candidate or employee information
            3. Research any additional context needed
            
            Provide structured meeting notes with:
            - Key discussion points
            - Relevant policies or procedures
            - Questions to ask
            - Action items
            """,
            agent=meeting_agent,
            tools=[doc_search, csv_search, google_search],
            expected_output="Structured meeting notes: Key discussion points; Relevant policies; Questions to ask; Action items"
        )
        
        # Create and run crew
        crew = Crew(
            agents=[meeting_agent],
            tasks=[meeting_task],
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        # Detect common authentication errors coming from litellm/crewai
        err_str = str(e)
        if 'AuthenticationError' in err_str or 'api_key' in err_str or 'OPENAI_API_KEY' in err_str:
            ok, llm_msg, detected = check_llm_config()
            masked = {k: ('SET' if v else None) for k, v in detected.items()}
            guidance = (
                "Authentication/runtime error when calling LLM.\n\n"
                "Possible fixes:\n"
                " - If you intend to use OpenAI, set the `OPENAI_API_KEY` environment variable.\n"
                " - If you intend to use Google Gemini, set `GEMINI_API_KEY` (or provider-specific credentials) and configure litellm to use Google.\n"
                " - After setting the key(s), restart this Streamlit app.\n\n"
                f"Detected keys (masked): {masked}\n\n"
                "Original error: " + err_str
            )
            return guidance

        return f"Error generating meeting notes: {err_str}"

def answer_faq(question):
    """Answer FAQ questions using company policies"""
    if not CREWAI_AVAILABLE:
        return "CrewAI is not available. Please install required dependencies."
    
    try:
        doc_search, _, google_search = initialize_tools()
        _, faq_agent, _ = create_hr_agents()
        
        if not all([doc_search, google_search, faq_agent]):
            return "Error initializing AI components."
        
        # Create task for FAQ answering
        faq_task = Task(
            description=f"""
            Answer this HR policy question: {question}
            
            Search the company's Employee Code of Conduct and other available documents 
            to provide an accurate, helpful answer. If the specific information isn't 
            available in the documents, use your general HR knowledge but indicate 
            when you're providing general guidance vs. company-specific policies.
            
            Provide a clear, professional response that includes:
            - Direct answer to the question
            - Relevant policy references if available
            - Any additional helpful context
            """,
            agent=faq_agent,
            tools=[doc_search, google_search],
            expected_output="FAQ answer: Direct response with policy references when available"
        )
        
        # Create and run crew
        crew = Crew(
            agents=[faq_agent],
            tasks=[faq_task],
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"Error answering question: {str(e)}"

def generate_email(email_request):
    """Generate professional HR emails"""
    if not CREWAI_AVAILABLE:
        return "CrewAI is not available. Please install required dependencies."
    
    try:
        doc_search, csv_search, google_search = initialize_tools()
        _, _, email_agent = create_hr_agents()
        
        if not all([email_agent]):
            return "Error initializing AI components."
        
        # Create task for email generation
        email_task = Task(
            description=f"""
            Draft a professional HR email based on this request: {email_request}
            
            Create a well-structured email that includes:
            - Appropriate subject line
            - Professional greeting
            - Clear, concise body content
            - Professional closing
            - Proper tone for the situation
            
            Make sure the email follows professional HR communication standards.
            """,
            agent=email_agent,
            tools=[doc_search, csv_search, google_search] if doc_search else [],
            expected_output="Email content: subject, greeting, body, and closing"
        )
        
        # Create and run crew
        crew = Crew(
            agents=[email_agent],
            tasks=[email_task],
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"Error generating email: {str(e)}"

def send_email(recipient, subject, body, smtp_host='smtp.gmail.com', smtp_port=465, use_ssl=True, debug=False):
    """Send email using configured SMTP.

    Parameters:
    - recipient, subject, body: email fields
    - smtp_host/smtp_port/use_ssl: transport control (use localhost:1025 for debug)
    - debug: when True, return detailed exception text for troubleshooting
    """
    try:
        # First try environment variables, then Streamlit secrets (for deployed apps)
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")

        # Streamlit deploys commonly store secrets in st.secrets
        try:
            if (not sender_email or not sender_password) and hasattr(st, 'secrets'):
                secrets = st.secrets
                if not sender_email:
                    sender_email = secrets.get('EMAIL_SENDER')
                if not sender_password:
                    sender_password = secrets.get('EMAIL_PASSWORD')
        except Exception:
            # If anything goes wrong accessing st.secrets, ignore and fall back to env
            pass

        if not sender_email or not sender_password:
            return "Email configuration missing. Please set EMAIL_SENDER and EMAIL_PASSWORD environment variables or add them to Streamlit secrets (.streamlit/secrets.toml)."
        
        # Create message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient
        msg.set_content(body)
        
        # Send email
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                try:
                    server.starttls(context=ssl.create_default_context())
                except Exception:
                    # starttls may fail on debug servers; ignore
                    pass
                server.login(sender_email, sender_password)
                server.send_message(msg)

        return "Email sent successfully!"

    except Exception as e:
        if debug:
            # Return a detailed error string for debugging in the UI
            import traceback
            return f"Error sending email: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return f"Error sending email: {str(e)}"

# Main UI
def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 EmpowerHR - AI-Powered HR Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🚀 HR Tools")
    selected_tool = st.sidebar.selectbox(
        "Choose an HR tool:",
        ["🏠 Home", "📝 Meeting Notes", "❓ FAQ Assistant", "ℹ️ About"]
    )
    
    # Home page
    if selected_tool == "🏠 Home":
        st.markdown('<div class="section-header">Welcome to EmpowerHR</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📝 Meeting Preparation")
            st.write("Generate comprehensive meeting notes and preparation materials for HR discussions.")
            if st.button("Start Meeting Prep", key="meeting_btn"):
                st.sidebar.selectbox("Choose an HR tool:", ["📝 Meeting Notes"], key="nav_meeting")
        
        with col2:
            st.markdown("### ❓ FAQ Assistant")
            st.write("Get instant answers to HR policy questions based on company documentation.")
            if st.button("Ask Questions", key="faq_btn"):
                st.sidebar.selectbox("Choose an HR tool:", ["❓ FAQ Assistant"], key="nav_faq")
        
        # with col3:
        #     # Email Generator disabled per user request
        #     # TODO: To re-enable the Email Generator, uncomment the lines below
        #     # st.markdown("### 📧 Email Generator")
        #     # st.write("Create professional HR emails for various scenarios and communications.")
        #     # if st.button("Generate Email", key="email_btn"):
        #     #     st.sidebar.selectbox("Choose an HR tool:", ["📧 Email Generator"], key="nav_email")
        #     # Non-empty placeholder so the `with` block has a valid body
        #     st.markdown("**Email Generator: disabled by user preference.**")
        
        # Recent activity
        st.markdown('<div class="section-header">Recent Activity</div>', unsafe_allow_html=True)
        if st.session_state.chat_history:
            for i, (tool, query, _) in enumerate(st.session_state.chat_history[-3:]):
                st.write(f"**{tool}:** {query[:100]}...")
        else:
            st.write("No recent activity. Start using the HR tools above!")
    
    # Meeting Notes tool
    elif selected_tool == "📝 Meeting Notes":
        st.markdown('<div class="section-header">Meeting Preparation Assistant</div>', unsafe_allow_html=True)
        
        st.write("Generate comprehensive meeting notes and preparation materials for your HR meetings.")
        
        meeting_input = st.text_area(
            "Describe your meeting or what you need to prepare for:",
            placeholder="e.g., Preparing for interview with John Smith for Senior Developer position, or Meeting about new remote work policy implementation",
            height=100
        )
        
        if st.button("Generate Meeting Notes", type="primary"):
            if meeting_input:
                with st.spinner("Preparing your meeting notes..."):
                    result = create_meeting_notes(meeting_input)
                    st.success("Meeting notes generated!")
                    st.markdown("### 📋 Your Meeting Notes")
                    st.write(result)
                    
                    # Save to history
                    st.session_state.chat_history.append(("Meeting Notes", meeting_input, result))
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Notes",
                        data=result,
                        file_name=f"meeting_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            else:
                st.warning("Please describe your meeting or preparation needs.")
    
    # FAQ Assistant
    elif selected_tool == "❓ FAQ Assistant":
        st.markdown('<div class="section-header">HR Policy FAQ Assistant</div>', unsafe_allow_html=True)
        
        st.write("Ask questions about company policies, procedures, and HR guidelines.")
        
        # Sample questions
        st.markdown("### 💡 Sample Questions")
        sample_questions = [
            "What is the company's remote work policy?",
            "How do I request time off?",
            "What are the guidelines for professional conduct?",
            "What is the process for reporting workplace issues?"
        ]
        
        selected_sample = st.selectbox("Or choose a sample question:", [""] + sample_questions)
        
        faq_question = st.text_input(
            "Ask your HR question:",
            value=selected_sample,
            placeholder="e.g., What is the dress code policy for remote workers?"
        )
        
        if st.button("Get Answer", type="primary"):
            if faq_question:
                with st.spinner("Searching company policies..."):
                    result = answer_faq(faq_question)
                    st.success("Answer found!")
                    st.markdown("### 💬 Answer")
                    st.write(result)
                    
                    # Save to history
                    st.session_state.chat_history.append(("FAQ", faq_question, result))
            else:
                st.warning("Please ask a question.")
    
    # Email Generator (disabled)
    # The Email Generator feature has been temporarily disabled per user request.
    # TODO: To re-enable, restore the block below and the `generate_email` function.
    # elif selected_tool == "📧 Email Generator":
    #     st.markdown('<div class="section-header">Professional Email Generator</div>', unsafe_allow_html=True)
    #     
    #     st.write("Generate professional HR emails for various scenarios.")
    #     
    #     # Email type selection
    #     email_type = st.selectbox(
    #         "Select email type:",
    #         [
    #             "Job Offer",
    #             "Interview Invitation",
    #             "Application Rejection",
    #             "Policy Update",
    #             "Meeting Invitation",
    #             "Performance Review",
    #             "Custom Request"
    #         ]
    #     )
    #     
    #     # Email details
    #     email_request = st.text_area(
    #         "Describe the email you need:",
    #         placeholder="e.g., Send a job offer to Sarah Johnson for Marketing Manager position with salary $75,000, start date January 15th",
    #         height=100
    #     )
    #     
    #     if st.button("Generate Email", type="primary"):
    #         if email_request:
    #             with st.spinner("Drafting your professional email..."):
    #                 full_request = f"Create a {email_type} email: {email_request}"
    #                 result = generate_email(full_request)
    #                 st.success("Email generated!")
    #                 st.markdown("### 📧 Generated Email")
    #                 st.code(result, language="text")
    #                 
    #                 # Save to history
    #                 st.session_state.chat_history.append(("Email", email_request, result))
    #                 # Parse subject and body so we can persist them across Streamlit reruns
    #                 lines = result.split('\n')
    #                 parsed_subject = None
    #                 parsed_body = result
    #                 if len(lines) > 0 and lines[0].lower().startswith('subject:'):
    #                     parsed_subject = lines[0].split(':', 1)[1].strip()
    #                     # Remove subject line and possible blank line after it
    #                     body_lines = lines[1:]
    #                     if len(body_lines) > 0 and body_lines[0].strip() == '':
    #                         body_lines = body_lines[1:]
    #                     parsed_body = '\n'.join(body_lines)

    #                 # Persist generated email in session state so Send Email works reliably
    #                 st.session_state.generated_email = result
    #                 st.session_state.generated_subject = parsed_subject or "HR Communication"
    #                 st.session_state.generated_body = parsed_body

    #                 # Send email option (uses persisted session_state values)
    #                 st.markdown("### 📤 Send Email")
    #                 col1, col2 = st.columns(2)
    #                 with col1:
    #                     recipient = st.text_input("Recipient email:", placeholder="recipient@company.com")
    #                 with col2:
    #                     subject = st.text_input("Subject:", value=st.session_state.generated_subject)

    #                 if st.button("Send Email"):
    #                     if recipient and subject:
    #                         body_to_send = st.session_state.generated_body or result
    #                         send_result = send_email(recipient, subject, body_to_send)
    #                         if "successfully" in send_result:
    #                             st.success(send_result)
    #                         else:
    #                             st.error(send_result)
    #                     else:
    #                         st.warning("Please provide recipient and subject.")

    #                 # Debug / Test sending options
    #                 with st.expander("Debug / Test Sending"):
    #                     use_local_smtp = st.checkbox("Use local SMTP debugging server (localhost:1025)", value=False)
    #                     if st.button("Send Email (Debug)"):
    #                         if recipient and subject:
    #                             if use_local_smtp:
    #                                 # When using a local SMTP debug server, credentials aren't needed
    #                                 debug_result = send_email(recipient, subject, body_to_send, smtp_host='localhost', smtp_port=1025, use_ssl=False, debug=True)
    #                             else:
    #                                 debug_result = send_email(recipient, subject, body_to_send, debug=True)

    #                             # Show detailed debug result
    #                             if debug_result and debug_result.startswith('Error'):
    #                                 st.error(debug_result)
    #                             else:
    #                                 st.success(debug_result)
    #                         else:
    #                             st.warning("Please provide recipient and subject.")
    #         else:
    #             st.warning("Please describe the email you need.")
    
    # About page
    elif selected_tool == "ℹ️ About":
        st.markdown('<div class="section-header">About EmpowerHR</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🚀 AI-Powered HR Assistant
        
        EmpowerHR is an intelligent HR assistant that helps streamline your human resources tasks using advanced AI technology.
        
        **Features:**
        - 📝 **Meeting Preparation**: Generate comprehensive notes and discussion points
        - ❓ **FAQ Assistant**: Instant answers based on company policies
        - 📧 **Email Generator**: Professional HR communications
        
        **Technology Stack:**
        - 🤖 **AI Models**: Gemini 1.5-Flash for intelligent responses
        - 🔍 **Search**: SerperDev for web search capabilities
        - 📄 **Document Processing**: Advanced document search and analysis
        - ☁️ **Deployment**: Streamlit Cloud for easy access
        
        **Security:**
        - 🔒 Environment variables for API keys
        - 🛡️ Secure document handling
        - 🔐 Professional email integration
        """)
        
        # System status
        st.markdown("### 🔧 System Status")
        col1, col2 = st.columns(2)
        
        with col1:
            if CREWAI_AVAILABLE:
                st.success("✅ CrewAI: Available")
            else:
                st.error("❌ CrewAI: Not Available")
            
            if os.getenv("GEMINI_API_KEY"):
                st.success("✅ Gemini API: Configured")
            else:
                st.error("❌ Gemini API: Not Configured")
        
        with col2:
            if os.getenv("SERPER_API_KEY"):
                st.success("✅ Search API: Configured")
            else:
                st.error("❌ Search API: Not Configured")
            
            if os.getenv("EMAIL_SENDER"):
                st.success("✅ Email: Configured")
            else:
                st.error("❌ Email: Not Configured")

if __name__ == "__main__":
    main()