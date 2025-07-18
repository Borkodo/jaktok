from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.video import Video
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import json
import os

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "video_inbox")
INDEX_JSON = os.path.join(os.path.dirname(__file__), "index.json")

def get_preview_path(video_path):
    return video_path.rsplit(".", 1)[0] + "_preview.jpg"

class VideoScreen(Screen):
    def __init__(self, video_path, **kwargs):
        super().__init__(**kwargs)
        print(f"[DEBUG] 🖼️ Creating screen for: {video_path}")
        self.video_path = video_path
        self.preview_path = get_preview_path(video_path)
        self.layout = FloatLayout(size_hint=(1,1), pos_hint={"x": 0, "y": 0})

        # Add background color (black)
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self.update_bg, pos=self.update_bg)

        # Add preview image if available
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

        # Add video (but keep it invisible for now)
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
            return False  # Stop polling
        return True  # Keep polling

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
        Window.fullscreen = 'auto'
        self.manager = ScreenManager(transition=SlideTransition(duration=0.3))
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
        self.touch_y = None
        return self.manager

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
