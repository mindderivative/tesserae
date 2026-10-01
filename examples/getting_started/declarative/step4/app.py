from pathlib import Path

from tesserae import App

from Counter_ViewModel import CounterViewModel

app = App(width=360, height=160, title="Counter")
app.load(Path(__file__).parent / "Counter_View.yaml", CounterViewModel)
app.show("Counter")
app.run()
