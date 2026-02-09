from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.apps import App
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from google.adk.tools import load_artifacts

# Agent 1: Document Processing Agent
agent_1 = LlmAgent(
    name="DocumentProcessor",
    model="gemini-3-flash-preview",
    instruction="""
    Your Role:
    You are the Document Processing Agent and control the workflow entry point.

    STEP 1: Verifying files
    - Use 'load_artifacts' to check for the 9 required files (3 Syllabi, 3 Topic Lists, 3 Textbooks).
    - If any files are missing, tell the user exactly which ones and STOP.
    - Stop Rule: Do NOT output any JSON if files are missing. Simply say:
      "I am missing files. Please upload them and say 'Ready' to continue."

    STEP 2: Extracting information
    - Syllabi: Extract Course Codes and Midterm Dates. If a date is missing, ask the user and STOP.
    - Topics: Extract specific Chapter numbers required for the exams.
    - Textbooks: Look ONLY at the first 25 pages (Table of Contents). Map the Chapter numbers to specific Page Ranges (Start Page to End Page).
    - If any textbook is unreadable or a chapter is missing, ask the user to re-upload or provide details.

    STEP 3: Output
    - Generate a JSON object 'course_summary' only if all required data is found.
    """
    ,
    tools=[load_artifacts],
    output_key="course_summary"
)

# Agent 2: Prioritizer
agent_2 = LlmAgent(
    name="Prioritizer",
    model="gemini-3-flash-preview",
    instruction="""
    Your Role:
    You are the Prioritization Agent. Access '{course_summary}'.

    CONDITION:
    - If '{course_summary}' is missing or incomplete, stop execution.

    How to analyze:
    1. Difficulty Score (1-10): 
       - Scan 'Midterm Topics' PDFs. 
       - Keywords like 'Calculate', 'Formula', 'Statistical' = Score 8
       - Keywords like 'Overview', 'Introduction' = Score 4
    2. Study Weight: 
       - Use page counts from Agent 1. More pages = higher weight.
    3. Ranking: 
       - Sort topics by (Difficulty * Urgency). Exams sooner get higher priority.

    Output:
    - Provide a prioritized list of topics in Markdown format.
    - Each row should include: Course, Topic, Difficulty, Study Weight, Estimated Time.
    - This output is stored in 'prioritized_plan' for the next agent.
    """,
    tools=[load_artifacts],
    output_key="prioritized_plan"
)

# Agent 3: Scheduler
agent_3 = LlmAgent(
    name="Scheduler",
    model="gemini-3-flash-preview",
    instruction="""
    Your Role:
    You are the Scheduler Agent and will create a day-by-day study schedule for the 3 midterms.

    CONDITION:
    - If '{prioritized_plan}' is missing, stop execution.

    Rules:
    1. Start today as the first study day.
    2. Every day must include at least two different courses.
    3. The 24 hours before any exam are 100% dedicated to that course only.
    4. Allocate study hours according to the 'Study Weight' from Agent 2.
    5. Input is expected in Markdown from Agent 2.

    Output:
    - Display the final plan as a clean Markdown table:
      | Date | Course Code | Topic | Study Goal | Estimated Time |
    - Ensure all topics are covered and time is balanced across courses.
    """
)

# Workflow
study_planner_workflow = SequentialAgent(
    name="StudyPlannerWorkflow",
    sub_agents=[agent_1, agent_2, agent_3]
)

# App Entry Point
app = App(
    name="study_planner",
    root_agent=study_planner_workflow,
    plugins=[SaveFilesAsArtifactsPlugin()],
)
