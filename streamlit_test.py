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
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Check if required packages are available
try:
    from crewai import Crew, Agent, Task, Process
    from crewai_tools import DOCXSearchTool, CSVSearchTool, TXTSearchTool, SerperDevTool
    CREWAI_AVAILABLE = True
    st.success("✅ CrewAI is available and loaded successfully!")
except ImportError as e:
    CREWAI_AVAILABLE = False
    st.error(f"❌ CrewAI not available: {str(e)}")
    st.info("🔧 Install with: `pip install crewai crewai-tools langchain langchain-google-genai`")

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

def generate_email_fallback(email_type, description):
    """Generate email using simple template when CrewAI is not available"""
    
    # Basic email templates
    templates = {
        "Interview Invitation": {
            "subject": "Interview Invitation - {position} Position",
            "template": """Dear {candidate_name},

Thank you for your interest in the {position} position at our company. We have reviewed your application and are impressed with your qualifications.

We would like to invite you to participate in an interview process. Based on your profile:

{candidate_summary}

Interview Details:
- Position: {position}
- Format: [To be confirmed - Virtual/In-person]
- Duration: Approximately 1 hour
- Next Steps: Please reply with your availability for the upcoming week

We look forward to discussing this opportunity with you in more detail.

Best regards,
HR Team
Company Name"""
        },
        "Job Offer": {
            "subject": "Job Offer - {position} Position",
            "template": """Dear {candidate_name},

We are pleased to extend an offer for the {position} position at our company.

Based on our evaluation:
{candidate_summary}

We believe you would be an excellent addition to our team.

Offer Details:
- Position: {position}
- Start Date: [To be discussed]
- Compensation: [To be discussed]
- Benefits: [Standard company benefits package]

Please review this offer and let us know your decision by [Date].

Congratulations and welcome to the team!

Best regards,
HR Team
Company Name"""
        },
        "Application Rejection": {
            "subject": "Thank you for your application - {position} Position",
            "template": """Dear {candidate_name},

Thank you for your interest in the {position} position and for taking the time to interview with us.

After careful consideration of all candidates:
{candidate_summary}

While your qualifications are impressive, we have decided to move forward with another candidate whose experience more closely aligns with our current needs.

We appreciate the time and effort you invested in the application process and encourage you to apply for future opportunities that match your skills and interests.

Best wishes for your job search.

Best regards,
HR Team
Company Name"""
        }
    }
    
    # Extract information from description
    candidate_name = "Candidate"  # Default
    position = "Software Engineer"  # Default
    
    # Try to extract candidate name (look for common patterns)
    lines = description.split('\n')
    for line in lines:
        if "Sarah" in line or "John" in line or "candidate" in line.lower():
            words = line.split()
            for i, word in enumerate(words):
                if word in ["Sarah", "John"] and i + 1 < len(words):
                    candidate_name = f"{word} {words[i+1]}"
                    break
            break
    
    # Try to extract position
    if "Software Engineer" in description:
        position = "Software Engineer"
    elif "Data Analyst" in description:
        position = "Data Analyst"
    elif "Marketing" in description:
        position = "Marketing Manager"
    
    # Get template
    template_data = templates.get(email_type, templates["Interview Invitation"])
    
    # Generate email
    subject = template_data["subject"].format(
        candidate_name=candidate_name,
        position=position
    )
    
    email_body = template_data["template"].format(
        candidate_name=candidate_name,
        position=position,
        candidate_summary=description[:500] + "..." if len(description) > 500 else description
    )
    
    return f"Subject: {subject}\n\n{email_body}"

def send_email(recipient, subject, body):
    """Send email using configured SMTP"""
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        if not sender_email or not sender_password:
            return "❌ Email configuration missing. Please set EMAIL_SENDER and EMAIL_PASSWORD environment variables."
        
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
        
        return "✅ Email sent successfully!"
        
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"

# Main UI
def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 EmpowerHR - AI-Powered HR Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🚀 HR Tools")
    selected_tool = st.sidebar.selectbox(
        "Choose an HR tool:",
        ["🏠 Home", "📝 Meeting Notes", "❓ FAQ Assistant", "📧 Email Generator", "⚙️ System Status"]
    )
    
    # Home page
    if selected_tool == "🏠 Home":
        st.markdown('<div class="section-header">Welcome to EmpowerHR</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📝 Meeting Preparation")
            st.write("Generate comprehensive meeting notes and preparation materials for HR discussions.")
            
        with col2:
            st.markdown("### ❓ FAQ Assistant")
            st.write("Get instant answers to HR policy questions based on company documentation.")
            
        with col3:
            st.markdown("### 📧 Email Generator")
            st.write("Create professional HR emails for various scenarios and communications.")
        
        # Feature highlight
        st.markdown('<div class="section-header">🌟 Key Features</div>', unsafe_allow_html=True)
        st.markdown("""
        - **AI-Powered**: Uses Gemini 1.5-Flash for intelligent responses
        - **Document Search**: Searches company policies and documentation
        - **Professional Templates**: Generate polished HR communications
        - **Easy Deployment**: Ready for Streamlit Cloud deployment
        """)
    
    # Email Generator (Main focus based on user request)
    elif selected_tool == "📧 Email Generator":
        st.markdown('<div class="section-header">Professional Email Generator</div>', unsafe_allow_html=True)
        
        st.write("Generate professional HR emails for various scenarios.")
        
        # Email type selection
        email_type = st.selectbox(
            "Select email type:",
            [
                "Interview Invitation",
                "Job Offer", 
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
            placeholder="e.g., Send interview invitation to Sarah Johnson for Software Engineer position based on her strong technical background...",
            height=200,
            value="""Sarah Johnson emerges as a promising contender for the Software Engineer position,
showcasing adeptness in Java, Python, and various development frameworks. Her
problem-solving skills shine through, demonstrating a logical approach to tackling
intricate coding challenges. However, there are occasional lapses in articulating
her thoughts clearly, suggesting room for improvement in communication during
technical discussions. Nevertheless, Sarah's eagerness for continuous learning
and professional growth is evident, evident through her engagement in online
courses and workshops, showcasing her adaptability to evolving industry trends.
With further refinement in communication and a focus on providing concrete
examples of collaboration and adaptability, Sarah holds the potential to excel in
the role."""
        )
        
        if st.button("Generate Email", type="primary"):
            if email_request:
                with st.spinner("Drafting your professional email..."):
                    if CREWAI_AVAILABLE:
                        # Use CrewAI when available (implement later)
                        result = "CrewAI functionality coming soon..."
                    else:
                        # Use fallback template system
                        result = generate_email_fallback(email_type, email_request)
                    
                    st.success("Email generated!")
                    st.markdown("### 📧 Generated Email")
                    st.code(result, language="text")
                    
                    # Parse subject and body for sending
                    lines = result.split('\n')
                    subject_line = lines[0].replace("Subject: ", "") if lines[0].startswith("Subject: ") else "HR Communication"
                    body_lines = lines[2:] if len(lines) > 2 else lines[1:]
                    email_body = '\n'.join(body_lines)
                    
                    # Send email option
                    st.markdown("### 📤 Send Email")
                    with st.expander("Email Sending Options"):
                        col1, col2 = st.columns(2)
                        with col1:
                            recipient = st.text_input("Recipient email:", placeholder="sarah.johnson@email.com")
                        with col2:
                            subject = st.text_input("Subject:", value=subject_line)
                        
                        if st.button("Send Email"):
                            if recipient and subject:
                                send_result = send_email(recipient, subject, email_body)
                                if "successfully" in send_result:
                                    st.success(send_result)
                                else:
                                    st.error(send_result)
                            else:
                                st.warning("Please provide recipient and subject.")
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Email",
                        data=result,
                        file_name=f"hr_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            else:
                st.warning("Please describe the email you need.")
    
    # Meeting Notes
    elif selected_tool == "📝 Meeting Notes":
        st.markdown('<div class="section-header">Meeting Preparation Assistant</div>', unsafe_allow_html=True)
        
        if not CREWAI_AVAILABLE:
            st.warning("⚠️ Full functionality requires CrewAI installation")
            st.code("pip install crewai crewai-tools langchain langchain-google-genai")
        
        st.write("Generate comprehensive meeting notes and preparation materials for your HR meetings.")
        
        meeting_input = st.text_area(
            "Describe your meeting or what you need to prepare for:",
            placeholder="e.g., Preparing for interview with John Smith for Senior Developer position",
            height=100
        )
        
        if st.button("Generate Meeting Notes", type="primary"):
            if meeting_input:
                st.info("🔧 Meeting notes functionality will be available after CrewAI installation")
            else:
                st.warning("Please describe your meeting or preparation needs.")
    
    # FAQ Assistant  
    elif selected_tool == "❓ FAQ Assistant":
        st.markdown('<div class="section-header">HR Policy FAQ Assistant</div>', unsafe_allow_html=True)
        
        if not CREWAI_AVAILABLE:
            st.warning("⚠️ Full functionality requires CrewAI installation")
        
        st.write("Ask questions about company policies, procedures, and HR guidelines.")
        
        faq_question = st.text_input(
            "Ask your HR question:",
            placeholder="e.g., What is the dress code policy for remote workers?"
        )
        
        if st.button("Get Answer", type="primary"):
            if faq_question:
                st.info("🔧 FAQ functionality will be available after CrewAI installation")
            else:
                st.warning("Please ask a question.")
    
    # System Status
    elif selected_tool == "⚙️ System Status":
        st.markdown('<div class="section-header">System Configuration & Status</div>', unsafe_allow_html=True)
        
        # Dependencies status
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📦 Dependencies")
            if CREWAI_AVAILABLE:
                st.success("✅ CrewAI: Available")
            else:
                st.error("❌ CrewAI: Not Available")
                st.code("pip install crewai crewai-tools")
            
            # Check other dependencies
            try:
                import streamlit
                st.success("✅ Streamlit: Available")
            except:
                st.error("❌ Streamlit: Not Available")
                
            try:
                from dotenv import load_dotenv
                st.success("✅ Python-dotenv: Available")
            except:
                st.error("❌ Python-dotenv: Not Available")
        
        with col2:
            st.markdown("### 🔑 Environment Variables")
            if os.getenv("GEMINI_API_KEY"):
                st.success("✅ Gemini API: Configured")
            else:
                st.error("❌ Gemini API: Not Configured")
            
            if os.getenv("SERPER_API_KEY"):
                st.success("✅ Search API: Configured")
            else:
                st.error("❌ Search API: Not Configured")
            
            if os.getenv("EMAIL_SENDER"):
                st.success("✅ Email: Configured")
            else:
                st.error("❌ Email: Not Configured")
        
        # Installation instructions
        st.markdown("### 🛠️ Installation Instructions")
        st.code("""
# Install all dependencies
pip install streamlit python-dotenv crewai crewai-tools langchain langchain-google-genai google-generativeai

# Set environment variables in .env file
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_email_app_password
OPENAI_MODEL_NAME=gemini/gemini-1.5-flash

# Run the application
streamlit run streamlit_app.py
        """)

if __name__ == "__main__":
    main()