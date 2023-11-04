import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

kivy.require('2.0.0')  # Replace with the version of Kivy you have installed


class MyApp(App):
    def build(self):
        # Configure the window
        self.title = "My Kivy App"
        self.icon = "icon.png"
        
        # Create a BoxLayout container
        container = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # Create a label
        label = Label(text="Hello, Kivy!")
        container.add_widget(label)
        
        # Create a button with a callback function
        button = Button(text="Click me!")
        button.bind(on_press=self.on_button_press)
        container.add_widget(button)

        return container

    def on_button_press(self, instance):
        print("Button clicked!")


if __name__ == "__main__":
    Window.fullscreen = True
    MyApp().run()