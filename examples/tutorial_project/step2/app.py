from pathlib import Path

from tesserae import App

HERE = Path(__file__).parent

app = App(width=420, height=520, title="Tasks", root=HERE, theme_seed=(0x0B, 0x6B, 0x58, 0xFF))
app.load("Main")  # Views/Main_View.yaml and ViewModels/Main_ViewModel.py
app.show("Main")
app.run()
