from pathlib import Path

from tesserae import App

HERE = Path(__file__).parent

app = App(
    width=420,
    height=520,
    title="Tasks",
    root=HERE,
    custom_theme="Brand",  # Themes/Brand_Theme.yaml: the colours, made from one seed
    stylesheet="Tasks",    # Styles/Tasks_Stylesheet.yaml: the look of every screen
)
app.load("Main")
app.show("Main")
app.run()
