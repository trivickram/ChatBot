import os
import smtplib
import ssl
from email.message import EmailMessage
import csv
from textwrap import dedent
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process
from tasks import MeetingPrepTasks
from agents import MeetingPrepAgents
from datetime import datetime, timedelta
from crewai_tools import DOCXSearchTool, CSVSearchTool, TXTSearchTool, tool, SerperDevTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys will be loaded from .env file
# GEMINI_API_KEY=your_gemini_api_key_here
# SERPER_API_KEY=your_serper_api_key_here  
# OPENAI_MODEL_NAME=gemini/gemini-1.5-flash

doc_search = DOCXSearchTool("docs/Employee-Code-of-Conduct.docx")
csv_search = CSVSearchTool('interview_data.csv')
google_search = SerperDevTool()

##########################This is for the onboarding section ######################################################
print("")
print("This is the onboarding use case")
name = input("Name: ")
role = input("Role: ")
receiver_email = input("Email: ")

researcher_agent = Agent(
        role="Research Specialist",
        goal='Research the role to find the best practices for the job role and provide links on how to be successful ',
        tools=[google_search],
        backstory=dedent("""\
          As a Research Specialist, your job is to search the web and come up with the best practices and methods
          to be successful at a specific job role and also provide useful links which talk about how to be successful
          in the partciular job role."""),
        verbose=True
      )

def research_task(role):
        return Task(
            description=dedent(f"""\
				generate the best practices and ways a person can successful at the given job role
                Job Role: {role}"""),
            expected_output=dedent("""\
				The best practices and things to do to be successful at the job role along with useful links for reference"""),
            agent=researcher_agent,
        )
set_research_task = research_task(role)

greet_agent = Agent(
        role="Personalized Message Sender",
        goal='Write a personalized message to person and welcome them into the company ',
        backstory=dedent("""\
          Your job is to write a personalized message to the new employee joining the company and talk about company culture and wish
          the employee success in the company"""),
        verbose=True
      )
def onboard_task(name,link):
        return Task(
            description=dedent(f"""\
				onboard the people by wishing good luck and ask them to review the code of conduct
                Employee Code of Conduct Link: {link},
                Name: {name}"""),
            expected_output=dedent("""\
				Output should be formatted like this:
                - Greeting and well wishes 
                - Ask to review Employee Code of Conduct with link 
                - Best Practices to be successful along with links
                - end it with
                Best Regards,
                John McEnroe,
                HR of Company XYZ"""),
            agent=greet_agent,
            context = [set_research_task]
        )
set_onboard_task = onboard_task(name,link="")

crew = Crew(agents=[researcher_agent,greet_agent], tasks=[set_research_task,set_onboard_task])
# Get your crew to work!
result = crew.kickoff()
print("######################")
print(result)



# Define email sender and receiver
email_sender = 'aneeshbsri@gmail.com'
email_password = "rsds xytr dtgz xrme"
email_receiver = receiver_email

# Set the subject and body of the email
subject = 'Welcome to Company XYZ!!!'
body = result

em = EmailMessage()
em['From'] = email_sender
em['To'] = email_receiver
em['Subject'] = subject
em.set_content(body)

# Add SSL (layer of security)
context = ssl.create_default_context()

# Log in and send the email
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(email_sender, email_password)
    smtp.sendmail(email_sender, email_receiver, em.as_string())

print("Email has been sent to",name,"Email:",receiver_email)


###############################################################################################################################################################







