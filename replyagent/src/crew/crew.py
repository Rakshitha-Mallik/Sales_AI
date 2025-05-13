from crewai import Crew
from .agents import EmailResponseAgent
from .tasks import EmailResponseTasks

class EmailResponseCrew:
    def __init__(self):
        self.response_agent = EmailResponseAgent().email_response_agent()
        self.tasks = EmailResponseTasks()

    def kickoff(self, state):
        print("### Responding to emails")
        for email in state['emails']:
            crew = Crew(
                agents=[self.response_agent],
                tasks=[],
                verbose=True
            )
            email_tasks = [
                self.tasks.respond_to_email_task(self.response_agent, email)
            ]
            crew.tasks.extend(email_tasks)
            result = crew.kickoff()
            state["action_required_emails"] = result
        return state
