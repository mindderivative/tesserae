from pathlib import Path

from tesserae import App

HERE = Path(__file__).parent

app = App(width=420, height=520, title="Tasks", root=HERE, theme_seed=(0x0B, 0x6B, 0x58, 0xFF))
app.bind(app.project.viewmodel("Main"))  # ViewModels/Main_ViewModel.py, the class MainViewModel
app.open_view("Main")  # Views/Main_View.yaml
app.show("Main")
app.run()
