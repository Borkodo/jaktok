from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import json
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from wifi_utils import scan_networks, connect_to_wifi, is_wifi_connected

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "video_inbox")
INDEX_JSON = os.path.join(os.path.dirname(__file__), "index.json")

from kivy.uix.widget import Widget
from kivy.graphics import PushMatrix, PopMatrix, Rotate, Translate

class RotatedRoot(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=90, origin=(0, 0))
            self.trans = Translate(Window.height, 0)
        with self.canvas.after:
            PopMatrix()


class WifiScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = FloatLayout()

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint=(0.9, 0.9), pos_hint={"center_x": 0.5, "center_y": 0.5})

        self.scroll = ScrollView(size_hint=(1, 0.6))
        self.network_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.network_list.bind(minimum_height=self.network_list.setter('height'))
        self.scroll.add_widget(self.network_list)

        self.status_label = Label(text="Select a network:", size_hint_y=None, height=30)
        self.password_input = TextInput(
            hint_text="Enter Wi-Fi password", password=True, multiline=False,
            size_hint_y=None, height=40
        )
        self.connect_button = Button(text="Connect", on_press=self.connect_to_selected, size_hint_y=None, height=40)

        self.layout.add_widget(self.scroll)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.password_input)
        self.layout.add_widget(self.connect_button)

        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        self.selected_ssid = None
        Clock.schedule_once(lambda dt: self.populate_networks(), 0.5)

    def populate_networks(self):
        ssids = scan_networks()
        print(f"[DEBUG] Found networks: {ssids}")
        for ssid in ssids:
            btn = Button(text=ssid, size_hint_y=None, height=40)
            btn.bind(on_release=self.make_ssid_selector(ssid))
            self.network_list.add_widget(btn)

    def make_ssid_selector(self, ssid):
        return lambda instance: self.select_ssid(ssid)

    def select_ssid(self, ssid):
        self.selected_ssid = ssid
        self.status_label.text = f"Selected: {ssid}"
        print(f"[DEBUG] Selected SSID: {ssid}")

    def connect_to_selected(self, instance):
        if not self.selected_ssid:
            self.status_label.text = "⚠️ Please select a network"
            return

        password = self.password_input.text
        print(f"[DEBUG] Trying to connect to {self.selected_ssid} with password '{password}'")

        success = connect_to_wifi(self.selected_ssid, password)
        self.status_label.text = "✅ Connected" if success else "❌ Connection failed"
        if success:
            App.get_running_app().restart_video_app()


def get_preview_path(video_path):
    return video_path.rsplit(".", 1)[0] + "_preview.jpg"

class VideoScreen(Screen):
    def __init__(self, video_path, **kwargs):
        super().__init__(**kwargs)
        print(f"[DEBUG] 🖼️ Creating screen for: {video_path}")
        self.video_path = video_path
        self.preview_path = get_preview_path(video_path)
        self.layout = FloatLayout(size_hint=(1,1), pos_hint={"x": 0, "y": 0})

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self.update_bg, pos=self.update_bg)

        if os.path.exists(self.preview_path):
            print(f"[DEBUG] ✅ Found preview: {self.preview_path}")
            self.preview = Image(
                source=self.preview_path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0}
            )
            self.layout.add_widget(self.preview)
        else:
            print(f"[WARN] ❌ Preview not found: {self.preview_path}")
            self.preview = None

        self.video = Video(
            source='',
            state='stop',
            options={'eos': 'loop'},
            allow_stretch=True,
            keep_ratio=True,
            opacity=0
        )
        self.bind(size=self.update_video_size, pos=self.update_video_size)
        self.layout.add_widget(self.video)

        self.add_widget(self.layout)
    def update_video_size(self, *args):
        self.video.size=self.size
        self.video.pos=self.pos
            
    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def check_video_ready(self, dt):
        if self.video.texture:
            print("[DEBUG] 🎬 First frame detected. Removing preview.")
            self.video.opacity = 1
            self.remove_preview()
            return False
        return True

    def remove_preview(self):
        if self.preview:
            print("[DEBUG] 🧹 Removing preview.")
            self.layout.remove_widget(self.preview)
            self.preview = None

    def on_enter(self):
        print(f"[DEBUG] ▶️ Entering screen: {self.video_path}")
        self.video.opacity = 0
        self.video.source = self.video_path
        self.video.state = 'play'
        Clock.schedule_interval(self.check_video_ready, 0.1)

    def on_leave(self):
        print(f"[DEBUG] ⏹️ Leaving screen: {self.video_path}")
        self.video.state = 'stop'



class VideoScrollerApp(App):
    def build(self):
        Window.show_cursor = False
        Window.fullscreen = 'auto'
        self.manager = ScreenManager(transition=SlideTransition(duration=0.3))

        if not is_wifi_connected():
            print("[INFO] 📶 No Wi-Fi detected. Showing Wi-Fi screen.")
            self.manager.add_widget(WifiScreen(name='wifi'))
            self.manager.current = 'wifi'
        else:
            self.setup_video_viewer()

        rotated_root = RotatedRoot()
        rotated_root.add_widget(self.manager)
        return rotated_root

    def setup_video_viewer(self):
        self.videos = self.load_videos()
        self.index = 0

        if self.videos:
            path = self.get_path(self.index)
            print(f"[DEBUG] 📦 Initial video: {path}")
            screen = VideoScreen(path, name='current')
            self.manager.add_widget(screen)
        else:
            print("❌ No videos found")

        Window.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)

    def restart_video_app(self):
        self.manager.clear_widgets()
        self.setup_video_viewer()
        self.manager.current = 'current'

    def load_videos(self):
        with open(INDEX_JSON) as f:
            videos = json.load(f)
        print(f"[DEBUG] 🎞️ Loaded {len(videos)} videos from index.")
        return sorted(videos, key=lambda x: x["timestamp"], reverse=True)

    def get_path(self, index):
        return os.path.join(VIDEO_FOLDER, self.videos[index]["filename"])

    def on_touch_down(self, window, touch):
        self.touch_y = touch.y

    def on_touch_up(self, window, touch):
        if self.touch_y is None:
            return
        delta = touch.y - self.touch_y
        if delta > 50:
            self.scroll(-1)
        elif delta < -50:
            self.scroll(1)
        self.touch_y = None

    def scroll(self, direction):
        new_index = self.index + direction
        if 0 <= new_index < len(self.videos):
            print(f"[DEBUG] 🔄 Scrolling from index {self.index} to {new_index}")
            self.index = new_index
            next_path = self.get_path(self.index)
            print(f"[DEBUG] 🔀 Next video path: {next_path}")
            next_screen = VideoScreen(next_path, name='next')
            self.manager.add_widget(next_screen)
            self.manager.transition.direction = 'down' if direction > 0 else 'up'
            self.manager.current = 'next'

            def cleanup(dt):
                try:
                    old_screen = self.manager.get_screen('current')
                    self.manager.remove_widget(old_screen)
                    print("[DEBUG] 🧹 Removed previous screen")
                except Exception as e:
                    print(f"[WARN] Could not remove old screen: {e}")
                next_screen.name = 'current'

            Clock.schedule_once(cleanup, 0.3)


if __name__ == "__main__":
    VideoScrollerApp().run()
