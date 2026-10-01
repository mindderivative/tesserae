from tesserae import App, View

app = App(width=360, height=160, title="Counter")
screen = View({"id": "root", "kind": "Container",
               "style": {"flex_direction": "vertical", "width": 360, "height": 160, "gap": 12, "padding": 16,
                         "background": "#1C1B1F"}},
              window=app.window)  # a screen: an empty box to put nodes in
app.register("Counter", screen, None)
app.show("Counter")

window = app.window
label = window.create("text", text="Count: 0", font_size=20, width=160, height=28, fill=(255, 255, 255, 255))
screen.root.add_child(label)

button = window.create("box", width=96, height=40, corner_radius=20, fill=(0x67, 0x50, 0xA4, 0xFF),
                       align_items="center", justify_content="center")
button.add_child(window.create("text", text="Count", font_size=16, width=44, height=20,
                               fill=(255, 255, 255, 255)))
screen.root.add_child(button)
app.run()
