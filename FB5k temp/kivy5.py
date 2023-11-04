import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse
from kivy.animation import Animation
from kivy.properties import ListProperty, StringProperty

kivy.require('2.0.0')


class ItemRow(BoxLayout):
    status = StringProperty()
    item_name = StringProperty()
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, status, item_name, color, **kwargs):
        super(ItemRow, self).__init__(**kwargs)
        self.status = status
        self.item_name = item_name
        self.color = color


class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.button_icon = 'arrow_up.png'
        self.text_displayed = False

        self.info_box = BoxLayout(orientation='vertical', size_hint=(1, None), pos_hint={'bottom': 0})
        self.info_box.bind(minimum_height=self.info_box.setter('height'))

        self.rows_container = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        self.rows_container.add_widget(self.info_box)

        self.arrow_button = Button(
            background_normal=self.button_icon,
            size_hint=(0.1, 0.1),
            pos_hint={'right': 1, 'bottom': 0}
        )
        self.arrow_button.bind(on_press=self.slide_window)

        self.add_widget(self.rows_container)
        self.add_widget(self.arrow_button)

    def slide_window(self, instance):
        if not self.text_displayed:
            anim = Animation(bottom=1, d=0.5)
            anim_button = Animation(y=self.arrow_button.y + self.height - self.arrow_button.height, d=0.5)
            self.button_icon = 'arrow_down.png'
        else:
            anim = Animation(bottom=0, d=0.5)
            anim_button = Animation(y=0, d=0.5)
            self.button_icon = 'arrow_up.png'

        anim.start(self.rows_container)
        anim_button.start(self.arrow_button)
        instance.background_normal = self.button_icon
        self.text_displayed = not self.text_displayed

    def add_item(self, status, item_name, color):
        row = ItemRow(status=status, item_name=item_name, color=color)
        self.info_box.add_widget(row)


class TouchScreenApp(App):
    def build(self):
        main_screen = MainScreen()
        main_screen.add_item("Added", "Item 1", [0, 1, 0, 1])
        main_screen.add_item("Removed", "Item 2", [1, 0, 0, 1])
        main_screen.add_item("Found", "Item 3", [0, 0, 1, 1])
        return main_screen


if __name__ == '__main__':
    TouchScreenApp().run()
