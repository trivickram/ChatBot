import os
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

csv_search = CSVSearchTool('interview_data.csv')
google_search = SerperDevTool()
# ##########################This is for the FAQ Section ######################################################

asked_question =  input("What is the question you would like to ask: ")
company_file = ""
doc_search = DOCXSearchTool(company_file)

faq_agent = Agent(
			role='Human Resource Employee',
			goal='Find the section of the document which contains relevant information and summarzie them. ',
			tools=[doc_search],
			backstory=dedent("""\
					As a HR Employee, your mission is to find which sections of the document contains the
                    relevant information and summarize those in a few sentences. If you can't find any keywords then just say 
                    I couldn't find anything in our company's policy regarding this topic . Kindly 
                    contact HR for information on this topic."""),
			verbose=True
		)
def summary_task(question):
		return Task(
			description=dedent(f"""\
				Find all the relevant areas of the document where the words from the question appear and
                summarize them in a few sentences.
				Question: {question}"""),
			expected_output=dedent("""\
				A few sentences summarizing the relevant infomration in the document which 
                conatins the keyword asked in the question. Starts each answer with Our company
                policy states that."""),
			agent=faq_agent
		)


summarize_task = summary_task(asked_question)

crew = Crew(agents=[faq_agent], tasks=[summarize_task])
# Get your crew to work!
result = crew.kickoff()

print("######################")
print(result)
##################################################################################################################################
