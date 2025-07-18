from kivy.app import App
from kivy.uix.video import Video
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
import json
import os

VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "video_inbox")
INDEX_JSON = os.path.join(os.path.dirname(__file__), "index.json")

class VideoScroller(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_list = self.load_videos()
        self.index = 0
        self.player = Video(source=self.get_path(), state='play', options={'eos': 'loop'})
        self.add_widget(self.player)
        self.touch_y = None

    def load_videos(self):
        with open(INDEX_JSON) as f:
            videos = json.load(f)
        return sorted(videos, key=lambda x: x["timestamp"], reverse=True)

    def get_path(self):
        return os.path.join(VIDEO_FOLDER, self.video_list[self.index]["filename"])

    def on_touch_down(self, touch):
        self.touch_y = touch.y

    def on_touch_up(self, touch):
        if not self.touch_y:
            return
        delta = touch.y - self.touch_y
        if delta > 50:
            self.scroll_up()
        elif delta < -50:
            self.scroll_down()
        self.touch_y = None

    def scroll_up(self):
        if self.index < len(self.video_list) - 1:
            self.index += 1
            self.load_video()

    def scroll_down(self):
        if self.index > 0:
            self.index -= 1
            self.load_video()

    def load_video(self):
        self.remove_widget(self.player)
        self.player = Video(source=self.get_path(), state='play', options={'eos': 'loop'})
        self.add_widget(self.player)


class VideoScrollerApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        return VideoScroller()


if __name__ == "__main__":
    VideoScrollerApp().run()
