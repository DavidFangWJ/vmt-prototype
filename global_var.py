from font_library import FontLibrary


FONT_LIBRARY = None


def initialize_font_library(chinese, western):
    global FONT_LIBRARY
    FONT_LIBRARY = FontLibrary(chinese, western)


def get_default_chinese_font():
    return FONT_LIBRARY.default_chinese


def get_default_western_font():
    return FONT_LIBRARY.default_western


def get_font_by_name(name):
    return FONT_LIBRARY.font_dict[name]


# 为了模拟DVI格式，我们要给每个“字体—字号”对设计唯一的序号。
FONT_ENCODINGS = {}


def get_font_encoding(typeface, size):
    if (typeface, size) in FONT_ENCODINGS.keys():
        return FONT_ENCODINGS[(typeface, size)]
    new_encoding = len(FONT_ENCODINGS) + 1
    FONT_ENCODINGS[(typeface, size)] = new_encoding
    return new_encoding
