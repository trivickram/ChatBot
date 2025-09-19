"""
Simple AI agent implementation without ChromaDB dependency
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class SimpleAgent:
    def __init__(self, role, goal, backstory):
        self.role = role
        self.goal = goal 
        self.backstory = backstory
        
        # Configure Gemini AI
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def execute_task(self, task_description):
        """Execute a task using Gemini AI"""
        if not self.model:
            return "Error: Gemini API key not configured"
        
        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        Context: {self.backstory}
        
        Task: {task_description}
        
        Please provide a comprehensive response based on your role and expertise.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                return """
## ⚠️ API Quota Exceeded

The daily AI usage limit has been reached. Please try again tomorrow.

*AI features will be available again when the quota resets.*
"""
            else:
                return f"Error: {str(e)}"

def create_simple_meeting_notes(user_input):
    """Generate meeting notes using simple AI agent"""
    agent = SimpleAgent(
        role="Senior HR Meeting Preparation Specialist",
        goal="Prepare comprehensive meeting notes and analysis for HR discussions",
        backstory="You analyze candidate information, company policies, and create structured meeting notes that help HR professionals conduct effective interviews and meetings."
    )
    
    task = f"""
    Prepare comprehensive meeting notes based on this request: {user_input}
    
    Provide structured meeting notes with:
    - Key discussion points
    - Relevant policies or procedures  
    - Questions to ask
    - Action items
    """
    
    return agent.execute_task(task)

def create_simple_faq_answer(question):
    """Answer FAQ using simple AI agent"""
    agent = SimpleAgent(
        role="HR Policy Expert",
        goal="Provide clear, accurate answers to HR policy questions",
        backstory="You are an expert in HR policies, employee relations, and workplace regulations. You provide clear, helpful guidance on HR matters."
    )
    
    task = f"""
    Answer this HR policy question: {question}
    
    Provide a clear, professional response that includes:
    - Direct answer to the question
    - Relevant policy considerations
    - Any additional helpful context
    """
    
    return agent.execute_task(task)

def create_simple_email(email_request):
    """Generate email using simple AI agent"""
    agent = SimpleAgent(
        role="Professional HR Communications Specialist", 
        goal="Draft professional, effective HR emails",
        backstory="You craft professional HR communications including offers, rejections, policy updates, and general correspondence."
    )
    
    task = f"""
    Draft a professional HR email based on this request: {email_request}
    
    Create a well-structured email that includes:
    - Appropriate subject line
    - Professional greeting
    - Clear, concise body content
    - Professional closing
    - Proper tone for the situation
    """
    
    return agent.execute_task(task)