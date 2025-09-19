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

# Import CrewAI components
try:
    from crewai import Crew, Agent, Task, Process
    from crewai_tools import DOCXSearchTool, CSVSearchTool, TXTSearchTool, SerperDevTool
    CREWAI_AVAILABLE = True
except (ImportError, RuntimeError, Exception) as e:
    import sys, traceback
    CREWAI_AVAILABLE = False
    tb = traceback.format_exc()
    print(f"CrewAI initialization failed: {e}")
    # Store error for display in UI
    CREWAI_ERROR = str(e)

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
        return f"""
## 📋 Meeting Notes - Fallback Mode

**Input:** {user_input}

### Key Discussion Points:
- Review candidate background and qualifications
- Assess cultural fit and alignment with company values
- Discuss role requirements and expectations
- Evaluate technical competencies and experience

### Questions to Ask:
- Can you walk me through your experience with [relevant technology/skill]?
- How do you handle challenging situations or conflicts?
- What motivates you in your work?
- Where do you see yourself in 5 years?

### Action Items:
- [ ] Review candidate resume and portfolio
- [ ] Prepare technical assessment questions
- [ ] Coordinate with team members for feedback
- [ ] Schedule follow-up interview if appropriate

### Policy References:
- Employee Code of Conduct
- Interview Guidelines and Best Practices
- Equal Opportunity Employment Policies

*Note: This is a simulated response. For AI-powered analysis, please resolve the system compatibility issues.*
"""
    
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
            expected_output="A comprehensive set of meeting notes including key discussion points, relevant policies, questions to ask, and action items formatted in a clear, structured manner.",
            agent=meeting_agent,
            tools=[doc_search, csv_search, google_search]
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
        error_str = str(e)
        if "quota" in error_str.lower() or "rate limit" in error_str.lower() or "429" in error_str:
            return """
## ⚠️ API Quota Exceeded

The Gemini AI service has reached its daily usage limit (50 requests per day for free tier).

### What happened?
- You've successfully used the AI features 50 times today
- Google's free tier has daily limits to prevent abuse
- The quota resets every 24 hours

### Options:
1. **Wait**: The quota will reset tomorrow and you can continue using the AI features
2. **Use Fallback Mode**: The app provides helpful templates and guidance without AI
3. **Upgrade**: Consider upgrading to a paid Google AI plan for higher limits

### Meanwhile:
- All other app features still work normally
- You can review your chat history
- Basic HR templates and guidance are available

*The AI features will be available again tomorrow when the quota resets.*
"""
        else:
            return f"Error generating meeting notes: {error_str}"

def answer_faq(question):
    """Answer FAQ questions using company policies"""
    if not CREWAI_AVAILABLE:
        return f"""
## ❓ HR Policy Response - Fallback Mode

**Your Question:** {question}

### General HR Guidance:

Based on common HR best practices, here are some general guidelines:

**Common HR Topics:**
- **Time Off:** Most companies have paid vacation, sick leave, and personal days. Check your employee handbook for specific policies.
- **Benefits:** Typically include health insurance, retirement plans, and professional development opportunities.
- **Code of Conduct:** Professional behavior, respect for colleagues, and adherence to company values are standard expectations.
- **Performance Reviews:** Usually conducted annually or bi-annually to discuss goals, achievements, and development areas.

### Next Steps:
- Consult your Employee Handbook for company-specific policies
- Contact your HR representative for detailed information
- Review any recent policy updates or announcements

*Note: This is general guidance only. For specific company policies and accurate information, please resolve the system compatibility issues to access AI-powered analysis of your company documents.*
"""
    
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
            expected_output="A clear, professional answer to the HR question including direct response, relevant policy references, and any additional helpful context.",
            agent=faq_agent,
            tools=[doc_search, google_search]
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
        error_str = str(e)
        if "quota" in error_str.lower() or "rate limit" in error_str.lower() or "429" in error_str:
            return """
## ⚠️ API Quota Exceeded

The daily AI usage limit has been reached. Please try again tomorrow or use the fallback guidance above.

For immediate assistance, you can:
- Consult your Employee Handbook
- Contact your HR representative directly
- Use general HR best practices as guidance

*AI-powered analysis will be available again when the quota resets.*
"""
        else:
            return f"Error answering question: {error_str}"

def generate_email(email_request):
    """Generate professional HR emails"""
    if not CREWAI_AVAILABLE:
        return f"""
## 📧 Professional HR Email - Fallback Mode

**Request:** {email_request}

---

**Subject:** Professional HR Communication

**Email Draft:**

Dear [Recipient Name],

I hope this email finds you well. I am writing regarding {email_request.lower()}.

[This is where the main content would be customized based on your specific request. Common HR email elements include:]

- Clear and professional tone
- Specific details and next steps
- Contact information for follow-up
- Relevant company policies or procedures

Please don't hesitate to reach out if you have any questions or need further clarification.

Best regards,
[Your Name]
[Your Title]
[Company Name]
[Contact Information]

---

*Note: This is a template response. For AI-generated, context-aware emails tailored to your specific needs, please resolve the system compatibility issues.*
"""
    
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
            expected_output="A complete professional HR email with subject line, greeting, body content, and closing that follows HR communication standards.",
            agent=email_agent,
            tools=[doc_search, csv_search, google_search] if doc_search else []
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
        error_str = str(e)
        if "quota" in error_str.lower() or "rate limit" in error_str.lower() or "429" in error_str:
            return """
## ⚠️ API Quota Exceeded

The daily AI usage limit has been reached. Please try again tomorrow or use the email template above.

The template provides a professional starting point that you can customize for your specific needs.

*AI-powered email generation will be available again when the quota resets.*
"""
        else:
            return f"Error generating email: {error_str}"

def send_email(recipient, subject, body):
    """Send email using configured SMTP"""
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        if not sender_email or not sender_password:
            return "Email configuration missing. Please set EMAIL_SENDER and EMAIL_PASSWORD environment variables."
        
        # Create message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient
        msg.set_content(body)
        
        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return "Email sent successfully!"
        
    except Exception as e:
        return f"Error sending email: {str(e)}"

# Main UI
def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 EmpowerHR - AI-Powered HR Assistant</h1>', unsafe_allow_html=True)
    
    # Display CrewAI status
    if not CREWAI_AVAILABLE:
        st.warning("⚠️ AI features are currently limited due to a system compatibility issue.")
        with st.expander("Technical Details"):
            st.error("CrewAI initialization failed due to ChromaDB compatibility issues on this platform.")
            st.info("**Fallback mode active:** Basic functionality is available with simulated responses.")
            if 'CREWAI_ERROR' in globals():
                st.code(f"Error: {CREWAI_ERROR}")
    else:
        # Add quota status info
        st.info("ℹ️ **AI Status:** Powered by Google Gemini (Free tier: 50 requests/day)")
        
    # Add general quota warning in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Usage Info")
    st.sidebar.info("Free tier: 50 AI requests per day\n\nIf quota is exceeded, fallback templates will be provided.")
    
    # Sidebar for navigation
    st.sidebar.title("🚀 HR Tools")
    selected_tool = st.sidebar.selectbox(
        "Choose an HR tool:",
        ["🏠 Home", "📝 Meeting Notes", "❓ FAQ Assistant", "📧 Email Generator", "ℹ️ About"]
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
        
        with col3:
            st.markdown("### 📧 Email Generator")
            st.write("Create professional HR emails for various scenarios and communications.")
            if st.button("Generate Email", key="email_btn"):
                st.sidebar.selectbox("Choose an HR tool:", ["📧 Email Generator"], key="nav_email")
        
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
    
    # Email Generator
    elif selected_tool == "📧 Email Generator":
        st.markdown('<div class="section-header">Professional Email Generator</div>', unsafe_allow_html=True)
        
        st.write("Generate professional HR emails for various scenarios.")
        
        # Email type selection
        email_type = st.selectbox(
            "Select email type:",
            [
                "Job Offer",
                "Interview Invitation",
                "Application Rejection",
                "Policy Update",
                "Meeting Invitation",
                "Performance Review",
                "Custom Request"
            ]
        )
        
        # Email details
        email_request = st.text_area(
            "Describe the email you need:",
            placeholder="e.g., Send a job offer to Sarah Johnson for Marketing Manager position with salary $75,000, start date January 15th",
            height=100
        )
        
        if st.button("Generate Email", type="primary"):
            if email_request:
                with st.spinner("Drafting your professional email..."):
                    full_request = f"Create a {email_type} email: {email_request}"
                    result = generate_email(full_request)
                    st.success("Email generated!")
                    st.markdown("### 📧 Generated Email")
                    st.code(result, language="text")
                    
                    # Save to history
                    st.session_state.chat_history.append(("Email", email_request, result))
                    
                    # Send email option
                    st.markdown("### 📤 Send Email")
                    col1, col2 = st.columns(2)
                    with col1:
                        recipient = st.text_input("Recipient email:", placeholder="recipient@company.com")
                    with col2:
                        subject = st.text_input("Subject:", placeholder="Job Offer - Marketing Manager Position")
                    
                    if st.button("Send Email"):
                        if recipient and subject:
                            send_result = send_email(recipient, subject, result)
                            if "successfully" in send_result:
                                st.success(send_result)
                            else:
                                st.error(send_result)
                        else:
                            st.warning("Please provide recipient and subject.")
            else:
                st.warning("Please describe the email you need.")
    
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