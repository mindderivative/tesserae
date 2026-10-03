from pathlib import Path

from tesserae import App

from Tasks_ViewModel import TasksViewModel

HERE = Path(__file__).parent

app = App(
    width=420,
    height=520,
    title="Tasks",
    custom_theme=HERE / "Brand_Theme.yaml",   # the colours: made from one seed
    stylesheet=HERE / "Tasks_Stylesheet.yaml",  # the look of every screen
)
app.load(HERE / "Tasks_View.yaml", TasksViewModel)
app.show("Tasks")
app.run()
