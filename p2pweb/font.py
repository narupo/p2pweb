from tkinter import font as tkfont

tk_default_font = None
basic_family = None
markdown_p = None
markdown_italic = None
markdown_strong = None
markdown_strong_italic = None
markdown_underline = None
markdown_overstrike = None


def init():
    global tk_default_font
    tk_default_font = tkfont.nametofont("TkDefaultFont")
    actual = tk_default_font.actual()

    global basic_family
    global markdown_p, markdown_italic, markdown_strong
    global markdown_strong_italic, markdown_underline, markdown_overstrike

    family = basic_family = actual['family']
    weight = actual['weight']
    slant = actual['slant']
    markdown_p = (family, 12, weight, slant)
    markdown_italic = (family, 12, weight, 'italic')
    markdown_strong = (family, 12, 'bold', slant)
    markdown_strong_italic = (family, 12, 'bold', 'italic')
    markdown_strong_italic = (family, 12, 'bold', 'italic')
    markdown_underline = (family, 12, weight, slant, 'underline')
    markdown_overstrike = (family, 12, weight, slant, 'normal', 'overstrike')


def get_headline_font(nsharp):
    if nsharp == 1:
        return (basic_family, 24, 'bold')
    elif nsharp == 2:
        return (basic_family, 22, 'bold')
    elif nsharp == 3:
        return (basic_family, 20, 'bold')
    elif nsharp == 4:
        return (basic_family, 18, 'bold')
    elif nsharp == 5:
        return (basic_family, 16, 'bold')
    else:
        return (basic_family, 14, 'bold')
