from tesserae import App

app = App(width=360, height=160, title="Counter")
window = app.window
window.root.set(flex_direction="vertical", gap=12, padding=16, fill=(0x1C, 0x1B, 0x1F, 0xFF))

label = window.create("text", text="Count: 0", font_size=20, width=160, height=28, fill=(255, 255, 255, 255))
window.root.add_child(label)

button = window.create("box", width=96, height=40, corner_radius=20, fill=(0x67, 0x50, 0xA4, 0xFF),
                       align_items="center")
button.add_child(window.create("text", text="Count", font_size=16, width=96, height=20,
                               fill=(255, 255, 255, 255), text_align="center"))
window.root.add_child(button)

app.run()
