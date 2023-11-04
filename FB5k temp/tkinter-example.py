import tkinter as tk

def on_button_click():
    button.config(text="You clicked me!")

app = tk.Tk()
app.title("Tkinter Example")

button = tk.Button(app, text="Click me", command=on_button_click)
button.pack()

app.mainloop()
