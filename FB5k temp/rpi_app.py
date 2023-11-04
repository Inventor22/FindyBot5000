import kivy
from kivy.app import App
from kivy.uix.button import Button

kivy.require('2.0.0')


class MyApp(App):
    def build(self):
        button = Button(text="Click me")
        button.bind(on_release=self.on_button_click)
        return button

    def on_button_click(self, instance):
        instance.text = "You clicked me!"


if __name__ == '__main__':
    MyApp().run()
