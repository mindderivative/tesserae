from pathlib import Path

from tesserae import App

from Tasks_ViewModel import TasksViewModel

HERE = Path(__file__).parent

app = App(width=420, height=520, title="Tasks", root=HERE, search=["."], theme_seed=(0x0B, 0x6B, 0x58, 0xFF))
app.bind(TasksViewModel)
app.open_view("Tasks")
app.show("Tasks")
app.run()
