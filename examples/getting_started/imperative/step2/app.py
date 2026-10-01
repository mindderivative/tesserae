from tesserae import App

app = App(width=360, height=160, title="Counter")
window = app.window
window.root.set(flex_direction="vertical", gap=12, padding=16, fill=(0x1C, 0x1B, 0x1F, 0xFF))

label = window.create("text", text="Count: 0", font_size=20, width=160, height=28, fill=(255, 255, 255, 255))
window.root.add_child(label)

app.run()
