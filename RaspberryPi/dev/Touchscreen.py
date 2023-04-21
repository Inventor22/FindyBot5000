import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.modalview import ModalView
from kivy.lang import Builder
from kivy.animation import Animation

kivy.require('2.0.0')

Builder.load_string("""
<ItemRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(50)

    canvas.before:
        Color:
            rgba: 1, 0, 0, 1 if self.is_added else (0, 1, 0, 1 if self.is_found else (0, 0, 1, 1))
        Ellipse:
            pos: self.pos
            size: dp(50), dp(50)

    Label:
        text: root.text
        size_hint_x: 0.9
        font_size: '16sp'

<MainWindow>:
    viewclass: 'ItemRow'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        spacing: dp(2)

<RaspTouchApp>:
    orientation: 'vertical'

    MainWindow:
        id: main_window

    Button:
        id: slide_button
        size_hint: None, None
        size: dp(50), dp(50)
        pos_hint: {'right': 1, 'y': 0}
        text: '\\u2191' if root.slide_up else '\\u2193'
        on_release: root.toggle_slide()
""")

class ItemRow(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty('')
    is_added = BooleanProperty(False)
    is_found = BooleanProperty(False)

class MainWindow(RecycleView):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.data = []

    def add_item(self, item_name, item_status):
        self.data.insert(0, {'text': f'{item_status} {item_name}', 'is_added': item_status == 'Added', 'is_found': item_status == 'Found'})

class RaspTouchApp(BoxLayout):
    slide_up = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(RaspTouchApp, self).__init__(**kwargs)
        self.ids.main_window.add_item('Item 1', 'Added')
        self.ids.main_window.add_item('Item 2', 'Removed')
        self.ids.main_window.add_item('Item 3', 'Found')

    def toggle_slide(self):
        anim = Animation(y=(self.height if not self.slide_up else 0), d=0.5)
        anim.start(self.ids.slide_button)
        self.slide_up = not self.slide_up

class TouchApp(App):
    def build(self):
        return RaspTouchApp()

if __name__ == '__main__':
    TouchApp().run()
``
