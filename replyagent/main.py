from src.graph import WorkFlow

app = WorkFlow().app
app.invoke({}, {"recursion_limit": 1000})