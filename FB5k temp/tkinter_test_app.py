import tkinter as tk

class SlideWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.withdraw()

        self.text = tk.Text(self)
        self.text.pack(fill="both", expand=True)

        self.bind("<Unmap>", self.on_unmap)

    def slide_up(self):
        self.update_idletasks()
        self.geometry(f"+0+{self.winfo_screenheight()}")
        self.deiconify()
        for i in range(self.winfo_screenheight(), 0, -10):
            self.geometry(f"+0+{i}")
            self.update_idletasks()

    def slide_down(self):
        for i in range(0, self.winfo_screenheight(), 10):
            self.geometry(f"+0+{i}")
            self.update_idletasks()
        self.withdraw()

    def on_unmap(self, event):
        self.master.toggle_button()

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Touchscreen App")

        self.sliding_window = SlideWindow(self)

        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True)

        self.toggle_button = tk.Button(self, text="▲", command=self.toggle_slide)
        self.toggle_button.pack(side="bottom", anchor="se")

        self.add_item("Item 1", "Added")
        self.add_item("Item 2", "Removed")
        self.add_item("Item 3", "Found")

    def toggle_slide(self):
        if self.sliding_window.winfo_viewable():
            self.sliding_window.slide_down()
            self.toggle_button.config(text="▲")
        else:
            self.sliding_window.slide_up()
            self.toggle_button.config(text="▼")

    def add_item(self, item_name, item_status):
        self.listbox.insert(0, f"{item_status} {item_name}")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
