from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
import json
import os

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "video_inbox")
INDEX_JSON = os.path.join(os.path.dirname(__file__), "index.json")

class VideoScreen(Screen):
    def __init__(self, video_path, **kwargs):
        super().__init__(**kwargs)
        self.video_path = video_path
        self.layout = FloatLayout()
        self.video = Video(
            source='',
            state='stop',
            options={'eos': 'loop'},
            allow_stretch=True,
            keep_ratio=True
        )
        self.layout.add_widget(self.video)
        self.add_widget(self.layout)

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self.update_bg, pos=self.update_bg)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def on_enter(self):
        self.video.source = self.video_path
        self.video.state = 'play'

    def on_leave(self):
        self.video.state = 'stop'



class VideoScrollerApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        self.manager = ScreenManager(transition=SlideTransition(duration=0.3))
        self.videos = self.load_videos()
        self.index = 0

        if self.videos:
            screen = VideoScreen(self.get_path(self.index), name='current')
            self.manager.add_widget(screen)
        else:
            print("❌ No videos found")

        Window.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        self.touch_y = None
        return self.manager

    def load_videos(self):
        with open(INDEX_JSON) as f:
            videos = json.load(f)
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
            self.index = new_index
            next_screen = VideoScreen(self.get_path(self.index), name='next')
            self.manager.add_widget(next_screen)
            self.manager.transition.direction = 'down' if direction > 0 else 'up'
            self.manager.current = 'next'

            def cleanup(dt):
                old_screen = self.manager.get_screen('current')
                self.manager.remove_widget(old_screen)
                next_screen.name = 'current'

            Clock.schedule_once(cleanup, 0.3)


if __name__ == "__main__":
    VideoScrollerApp().run()
