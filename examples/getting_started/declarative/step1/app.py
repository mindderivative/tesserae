from pathlib import Path

from tesserae import App

HERE = Path(__file__).parent

app = App(width=360, height=160, title="Counter")
app.open_view(HERE / "Counter_View.yaml")
app.show("Counter")
app.run()
