from pathlib import Path

from tesserae import App

app = App(width=360, height=160, title="Counter")
view = app.build_view(Path(__file__).parent / "Counter_View.yaml")
app.register("Counter", view, None)  # a screen with no ViewModel yet
app.show("Counter")
app.run()
