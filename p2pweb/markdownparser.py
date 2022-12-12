import tkinter as tk
from PIL import Image, ImageTk
import io
import os
import webbrowser
from p2pweb import font
from p2pweb.resource import Resource
from p2pweb.color import Color
from p2pweb import gui


class MarkdownParser:
    def __init__(
        self,
        context,
        tk_text_widget,
    ):
        self.context = context
        self.text = tk_text_widget
        self.text.tag_config('red', foreground='red')
        self.text.tag_config('p', font=font.markdown_p)
        self.text.tag_config('italic', font=font.markdown_italic)
        self.text.tag_config('strong', font=font.markdown_strong)
        self.text.tag_config('strong_italic', font=font.markdown_strong_italic)
        self.text.tag_config('list_digit', font=font.markdown_strong)
        self.text.tag_config('inyo', background='#ddd')
        self.text.tag_config('overstrike', font=font.markdown_overstrike)

    def parse(self, content):
        try:
            self._parse(content)
        except BaseException as e:
            print(e)
            self.text.insert(tk.END, 'マークダウンのパースに失敗しました。\n', 'red')
            raise e

    def _parse(self, content):
        self.content = content.replace('\r\n', '\n').rstrip() + '\n'
        self.clen = len(self.content)
        self.i = 0
        m = 0

        while self.i < self.clen:
            c1 = c2 = c3 = c4 = c5 = ''

            c1 = self.content[self.i]
            if self.i < self.clen - 1:
                c2 = self.content[self.i + 1]
            if self.i < self.clen - 2:
                c3 = self.content[self.i + 2]
            if self.i < self.clen - 3:
                c4 = self.content[self.i + 3]
            if self.i < self.clen - 4:
                c5 = self.content[self.i + 4]

            b2 = c1 + c2
            b3 = c1 + c2 + c3
            b5 = c1 + c2 + c3 + c4 + c5

            if m == 0:  # ここはいつも改行の1つ後に来る
                if c1 == '#':
                    self.parse_headline()
                elif b3 == '- [':
                    self.parse_checkbox()
                elif b2 == '* ' or self.is_digit_list():
                    self.parse_list()
                elif b3 == '---' or b3 == '***' or \
                        b5 == '- - -' or b5 == '* * *':
                    self.parse_hr()
                elif b3 == '```':
                    self.parse_code_block()
                elif b2 == '![':
                    self.parse_image()
                elif c1 == '>':
                    self.parse_inyo()
                else:
                    self.parse_line()

            self.i += 1

    def parse_overstrike(self):
        m = 0
        buf = ''

        while self.i < self.clen:
            c = self.content[self.i]

            if m == 0:
                if c == '~':
                    m = 10
                else:
                    break
            elif m == 10:
                if c == '~':
                    m = 20
                else:
                    break
            elif m == 20:
                if c == '~':
                    m = 30
                elif c == '\n':
                    break
                else:
                    buf += c
            elif m == 30:
                if c == '~':
                    break
                else:
                    break

            self.i += 1

        if len(buf):
            self.text.insert(tk.END, buf, 'overstrike')

    def parse_link(self):
        m = 0
        text = ''
        url = ''

        while self.i < self.clen:
            c = self.content[self.i]

            if m == 0:
                if c == '[':
                    m = 10
                else:
                    break
            elif m == 10:
                if c == ']':
                    m = 20
                elif c == '\n':
                    break
                else:
                    text += c
            elif m == 20:
                if c == '(':
                    m = 30
                else:
                    break
            elif m == 30:
                if c == ')':
                    break
                else:
                    url += c

            self.i += 1

        if len(text) and len(url):
            label = gui.Label(
                self.text,
                text=text,
                font=font.markdown_underline,
                foreground=Color.LINK_FG,
                background=Color.LINK_BG,
                cursor='hand2',
            )
            label.bind('<Button-1>', lambda ev: self.jump_to_link(label, url))
            self.text.window_create(
                tk.END,
                window=label,
            )

    def jump_to_link(self, label, url):
        print('jump_to_link')
        label.config(foreground=Color.LINK_VISITED_FG)
        self.context.dispatch('jump_to_link', url=url)
        # webbrowser.open_new(url.strip())

    def parse_image(self):
        m = 0
        alt = ''
        path = ''
        size = ''

        while self.i < self.clen:
            c = self.content[self.i]
            if m == 0:
                if c == '!':
                    m = 10
                else:
                    break
            elif m == 10:
                if c == '[':
                    m = 20
                else:
                    break
            elif m == 20:
                if c == ']':
                    m = 30
                elif c == '\n':
                    break
                else:
                    alt += c
            elif m == 30:
                if c == '(':
                    m = 40
                else:
                    break
            elif m == 40:
                if c == ')':
                    m = 50
                elif c == '\n':
                    break
                else:
                    path += c
            elif m == 50:
                if c == '\n':
                    break
                elif c == '(':
                    m = 60
            elif m == 60:
                if c == ')':
                    m = 70
                else:
                    size += c
            elif m == 70:
                if c == '\n':
                    break
            
            self.i += 1

        if len(path):
            try:
                htpp_response = self.context.web_engine.get(path)
            except BaseException as e:
                self.text.insert(tk.END, str(e) + '\n', 'red')
                raise e
            else:
                try:
                    image = Image.open(io.BytesIO(htpp_response.content))
                except BaseException as e:
                    self.text.insert(tk.END, '画像が開けませんでした。\n', 'red')
                    raise e
                else:
                    if len(size):
                        toks = size.split(' ')
                        if len(toks) == 2:
                            try:
                                w, h = int(toks[0]), int(toks[1])
                            except ValueError:
                                pass
                            else:
                                image.thumbnail((w, h))
                    image = ImageTk.PhotoImage(image)
                    resource = Resource.get_instance()
                    resource.add_markdown_image(image)
                    self.text.image_create(tk.END, image=image)
                    self.text.insert(tk.END, '\n')
                    if len(alt):
                        self.text.insert(tk.END, alt + '\n', 'p')

    def look_at_newline(self, target):
        i = self.i + 1
        tarlen = len(target)
        clen = len(self.content)

        while i < clen:
            found = True
            for j in range(tarlen):
                k = i + j
                if self.content[k] == target[j]:
                    found = False
                    break
            if found:
                return True

            if self.content[i] == '\n':
                break

            i += 1

        return False

    def parse_checkbox(self):
        m = 0

        while self.i < self.clen:
            c = self.content[self.i]

            if m == 0:
                if c == '[':
                    m = 10
            elif m == 10:
                if c == ' ':
                    m = 20
                elif c == ']':
                    self.i -= 1
                    m = 20
                elif c == 'x' or c == 'X':
                    m = 30
                else:
                    break
            elif m == 20:
                if c == ']':
                    self.text.image_create(
                        tk.END,
                        image=Resource.get_instance().html_checkbox,
                    )
                    self.i += 1
                    self.parse_line()
                    break
                else:
                    break
            elif m == 30:
                if c == ']':
                    self.text.image_create(
                        tk.END,
                        image=Resource.get_instance().html_checkbox_checked,
                    )
                    self.i += 1
                    self.parse_line()
                    break
                else:
                    break

            self.i += 1

    def parse_inyo(self):
        m = 0
        n = 0

        while self.i < self.clen:
            c = self.content[self.i]
            if m == 0:
                if c == '>':
                    n += 1
                    m = 10
                else:
                    break
            elif m == 10:
                if c == '>':
                    n += 1
                else:
                    self.create_inyo_head(n)
                    self.parse_line(foreground='#555')
                    break

            self.i += 1

    def create_inyo_head(self, n):
        for _ in range(n):
            self.text.insert(tk.END, ' ', 'inyo')
            self.text.insert(tk.END, '  ')

    def is_digit_list(self):
        i = self.i
        m = 0

        while i < self.clen:
            c = self.content[i]
            if m == 0:
                if c.isdigit():
                    m = 10
                else:
                    return False
            elif m == 10:
                if c.isdigit():
                    pass
                elif c == '.':
                    return True
                else:
                    return False
            i += 1

        return False

    def parse_code_block(self):
        m = 0
        buf = ''

        while self.i < self.clen:
            c1 = c2 = c3 = ''
            c1 = self.content[self.i]
            if self.i < self.clen - 1:
                c2 = self.content[self.i + 1]
            if self.i < self.clen - 2:
                c3 = self.content[self.i + 2]

            b3 = c1 + c2 + c3

            if m == 0:
                if b3 == '```':
                    m = 10
                    self.i += 2
                else:
                    break
            elif m == 10:
                if c1 == '\n':
                    self.i -= 1
                    m = 20
            elif m == 20:
                if b3 == '```':
                    self.i += 2
                    m = 30
                else:
                    buf += c1
            elif m == 30:
                if c1 == '\n':
                    break

            self.i += 1

        if len(buf):
            if buf[0] == '\n':
                buf = buf[1:]
            if buf[-1] == '\n':
                buf = buf[:-1]

        label = gui.Label(
            self.text,
            text=buf,
            background='#eee',
            foreground='#333',
            font=font.markdown_p,
        )
        self.text.window_create(
            tk.END,
            window=label,
        )
        self.text.insert(tk.END, '\n')

    def parse_hr(self):
        m = 0
        while self.i < self.clen:
            c1 = self.content[self.i]
            if m == 0:
                if c1 == '\n':
                    break

            self.i += 1

        label = gui.Label(
            self.text,
            text='-' * 80,
        )
        self.text.window_create(
            tk.END,
            window=label,
        )
        self.text.insert(tk.END, '\n')

    def parse_strong(self):
        m = 0
        buf = ''
        typ = ''

        while self.i < self.clen:
            c1 = c2 = c3 = ''

            c1 = self.content[self.i]
            if self.i < self.clen - 1:
                c2 = self.content[self.i + 1]
            if self.i < self.clen - 2:
                c3 = self.content[self.i + 2]

            b2 = c1 + c2
            b3 = c1 + c2 + c3

            if m == 0:
                if b3 == '***':
                    self.i += 2
                    m = 300
                    typ = '***'
                elif b2 == '**':
                    self.i += 1
                    m = 200
                    typ = '**'
                elif c1 == '*':
                    m = 100
                    typ = '*'
                else:
                    break
            elif m == 100:
                if c1 == '*':
                    break
                elif c1 == '\n':
                    break
                else:
                    buf += c1
            elif m == 200:
                if b2 == '**':
                    self.i += 1
                    break
                elif c1 == '\n':
                    break
                else:
                    buf += c1
            elif m == 300:
                if b3 == '***':
                    self.i += 2
                    break
                elif c1 == '\n':
                    break
                else:
                    buf += c1

            self.i += 1

        if typ == '*':
            self.text.insert(tk.END, buf.strip(), 'italic')
        elif typ == '**':
            self.text.insert(tk.END, buf.strip(), 'strong')
        else:
            self.text.insert(tk.END, buf.strip(), 'strong_italic')

    def parse_list(self):
        m = 0
        buf = ''
        nindent = 0

        while self.i < self.clen:
            c1 = c2 = c3 = c4 = ''
            c1 = self.content[self.i]
            if self.i < self.clen - 1:
                c2 = self.content[self.i + 1]
            if self.i < self.clen - 2:
                c3 = self.content[self.i + 2]
            if self.i < self.clen - 3:
                c4 = self.content[self.i + 3]

            block4 = c1 + c2 + c3 + c4

            if m == 0:
                if c1 == '*':
                    buf = ''
                    self.text.image_create(
                        tk.END,
                        image=Resource.get_instance().html_list_normal,
                    )
                    self.i += 1
                    self.parse_line()
                elif c1.isdigit():
                    m = 100
                    buf = c1
                elif c1 == '\t':
                    m = 20
                    buf = ''
                    nindent += 1
                elif block4 == '    ':
                    m = 20
                    buf = ''
                    nindent += 1
                    self.i += 3
                else:
                    self.i -= 1
                    break
            elif m == 20:
                if c1 == '*':
                    indent = nindent * '    '
                    self.text.insert(tk.END, indent)
                    self.text.image_create(
                        tk.END,
                        image=Resource.get_instance().html_list_normal,
                    )
                    self.i += 1
                    self.parse_line()
                    nindent = m = 0
                elif c1.isdigit():
                    buf += c1
                    m = 150
                elif block4 == '    ':
                    self.i += 3
                    nindent += 1
                elif c1 == '\t':
                    nindent += 1
                else:
                    nindent = 0
                    break
            elif m == 100:
                if c1.isdigit():
                    buf += c1
                elif c1 == '.':
                    buf += c1
                    self.text.insert(tk.END, buf, 'list_digit')
                    buf = ''
                    self.i += 1
                    self.parse_line()
                    m = 0
                else:
                    m = 0
                    buf = ''
            elif m == 150:
                if c1.isdigit():
                    buf += c1
                elif c1 == '.':
                    indent = nindent * '     '
                    buf += c1
                    text = indent + buf
                    self.text.insert(tk.END, text, 'list_digit')
                    buf = ''
                    self.i += 1
                    self.parse_line()
                    m = 0
                    nindent = 0
                else:
                    m = 0
                    buf = ''
            
            self.i += 1

    def parse_line(self, foreground=None):
        line = ''

        def insert_line():
            nonlocal line
            if len(line):
                self.text.insert(tk.END, line, 'p')
                line = ''

        while self.i < self.clen:
            c1 = c2 = c3 = ''
            c1 = self.content[self.i]
            if self.i < self.clen - 1:
                c2 = self.content[self.i + 1]
            if self.i < self.clen - 2:
                c3 = self.content[self.i + 2]

            b2 = c1 + c2
            b3 = c1 + c2 + c3

            if c1 == '\n':
                line += c1
                break
            elif (c1 == '*' and self.look_at_newline('*')) or \
                 (b2 == '**' and self.look_at_newline('**')) or \
                 (b3 == '***' and self.look_at_newline('***')):
                insert_line()
                self.parse_strong()
            elif (b2 == '~~' and self.look_at_newline('~~')):
                insert_line()
                self.parse_overstrike()
            elif c1 == '`':
                insert_line()
                self.parse_code()
            elif c1 == '[':
                insert_line()
                self.parse_link()
            else:
                line += c1
            self.i += 1

        if foreground:
            self.text.tag_config('color', foreground=foreground)
            self.text.insert(tk.END, f'{line}', 'color')
        else:
            self.text.insert(tk.END, f'{line}', 'p')

    def parse_code(self):
        m = 0
        buf = ''

        while self.i < self.clen:
            c = self.content[self.i]
            if m == 0:
                if c == '`':
                    m = 10
                else:
                    break
            elif m == 10:
                if c == '`':
                    break
                else:
                    buf += c

            self.i += 1

        self.text.window_create(
            tk.END,
            window=gui.Label(
                self.text,
                text=buf,
                font=font.markdown_p,
                background='#eee',
                foreground='#333',
            )
        )

    def parse_headline(self):
        nsharp = 0
        buf = ''
        m = 0

        while self.i < self.clen:
            c = self.content[self.i]
            if m == 0:
                if c == '#':
                    nsharp += 1
                elif c == '\n':
                    break
                else:
                    buf += c
                    m = 10
            elif m == 10:
                if c == '\n':
                    break
                else:
                    buf += c
            self.i += 1

        text = buf.strip() + '\n'
        self.text.tag_config('headline', font=font.get_headline_font(nsharp))
        self.text.insert(tk.END, text, 'headline')
