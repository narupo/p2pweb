import tkinter as tk


class Resource:
    def __init__(self):
        pass

    @staticmethod
    def get_instance():
        global _instance
        return _instance

    def load(self):
        self.markdown_images = []
        self.html_list_normal = tk.PhotoImage(file='resource/html_list_normal.png')
        self.html_list_white = tk.PhotoImage(file='resource/html_list_white.png')
        self.html_checkbox = tk.PhotoImage(file='resource/html_checkbox.png')
        self.html_checkbox_checked = tk.PhotoImage(file='resource/html_checkbox_checked.png')

    def add_markdown_image(self, image):
        self.markdown_images.append(image)

    def clear_markdown_images(self):
        self.markdown_images = []


_instance = Resource()
