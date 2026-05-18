import os
from crewai import Agent, Task, Crew, Process, LLM
from db_utils import fetch_current_schema
from dotenv import load_dotenv

load_dotenv()

# Initialize the LLM using Groq's newest model
my_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.1
)

def run_schema_evolution(user_request: str) -> str:
    """Orchestrates the agents to process the schema evolution request."""
    
    # 1. Fetch current schema to provide context to the agents
    try:
        current_schema = fetch_current_schema()
    except Exception as e:
        return f"Database connection error: {str(e)}"

    # --- AGENT DEFINITIONS ---
    
    schema_analyst = Agent(
        role='Database Schema Analyst',
        goal='Analyze the current database schema and identify dependencies, relationships, and constraints.',
        backstory='An expert database administrator with deep knowledge of PostgreSQL, normalization, and relational integrity.',
        verbose=True,
        allow_delegation=False,
        llm=my_llm
    )

    backup_specialist = Agent(
        role='Database Backup Specialist',
        goal='Ensure a data safety net exists by creating temporary backup tables of any table being modified or dropped.',
        backstory='A cautious DBA who never performs a migration without a fallback. Specializes in "CREATE TABLE ... AS SELECT" patterns.',
        verbose=True,
        allow_delegation=False,
        llm=my_llm
    )

    migration_planner = Agent(
        role='Migration Planning Engineer',
        goal='Draft secure, efficient SQL migration scripts based on user requests and schema analysis.',
        backstory='A senior backend developer specializing in safe database migrations, zero-downtime deployments, and avoiding data loss.',
        verbose=True,
        allow_delegation=False,
        llm=my_llm
    )

    validation_agent = Agent(
        role='Database Validation & Safety Agent',
        goal='Review migration plans for data loss risks, constraint violations, and syntax errors.',
        backstory='A strict QA database engineer who prevents bad SQL from ruining production databases. Focuses on rollbacks and safety checks.',
        verbose=True,
        allow_delegation=False,
        llm=my_llm
    )

    # --- TASK DEFINITIONS ---

    analysis_task = Task(
        description=f"""Analyze the following user request: '{user_request}'
        against the current database schema:
        {current_schema}
        Identify exactly which tables and columns are affected, and list any potential foreign key or data integrity dependencies.""",
        expected_output="A detailed report mapping the requested changes to the existing schema, highlighting tables, columns, and dependencies involved.",
        agent=schema_analyst
    )

    backup_task = Task(
        description=f"""Using the output from the Schema Analyst, identify the tables involved in this request: '{user_request}'. 
        Generate PostgreSQL SQL to create temporary backup copies of these tables (e.g., table_name_backup) and copy the data over.""",
        expected_output="A SQL script to create backup versions of the affected tables and insert the existing data into them.",
        agent=backup_specialist,
        context=[analysis_task]
    )

    migration_task = Task(
        description="""Using the outputs from the Analyst and Backup Specialist, generate the exact PostgreSQL SQL queries needed to perform the migration. 
        Ensure you include both the 'UP' migration (applying the change) and the 'DOWN' migration (rollback). 
        IMPORTANT: Include the Backup Specialist's backup SQL at the very beginning of the UP migration!""",
        expected_output="A set of raw PostgreSQL SQL scripts divided into UP MIGRATION and DOWN MIGRATION blocks.",
        agent=migration_planner,
        context=[analysis_task, backup_task]
    )

    validation_task = Task(
        description="""Review the generated migration scripts. Check for:
        1. Did the Backup Specialist include a data backup step?
        2. Potential data loss (e.g., dropping columns without backing up data).
        3. Syntax errors in PostgreSQL.
        4. Missing foreign key constraints or orphaned records.
        Provide a final safety score (0-100) and a brief justification.""",
        expected_output="A safety report including a Safety Score, Risk Analysis, and the final approved SQL scripts.",
        agent=validation_agent,
        context=[migration_task]
    )

    # --- CREW SETUP ---

    evolution_crew = Crew(
        agents=[schema_analyst, backup_specialist, migration_planner, validation_agent],
        tasks=[analysis_task, backup_task, migration_task, validation_task],
        process=Process.sequential,
        verbose=True
    )

    # Execute the workflow
    result = evolution_crew.kickoff()
    return result