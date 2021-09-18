from enum import Enum
from tokenizer import TokenType
from global_var import get_default_chinese_font, get_default_western_font, get_font_encoding


# 字体处理

CHINESE_FONT_SIZE = 0
WESTERN_FONT_SIZE = 0
CHINESE_SHIFT = 0

CHINESE_FONT = None
WESTERN_FONT = None


def set_chinese_font(font):
    global CHINESE_FONT, CHINESE_SHIFT
    CHINESE_FONT = font
    asc_real = font.ascent / font.upm
    CHINESE_SHIFT = (asc_real - 0.88) * CHINESE_FONT_SIZE


def set_western_font(font):
    global WESTERN_FONT, WESTERN_FONT_SIZE
    WESTERN_FONT = font
    cap_real = font.caps_height
    cap_desire = font.upm * 0.72
    WESTERN_FONT_SIZE = CHINESE_FONT_SIZE * cap_desire / cap_real


def set_font_size(size):
    global CHINESE_FONT_SIZE, WESTERN_FONT_SIZE, CHINESE_SHIFT

    CHINESE_FONT_SIZE = size
    cap_real = WESTERN_FONT.caps_height
    cap_desire = WESTERN_FONT.upm * 0.72
    WESTERN_FONT_SIZE = size * cap_desire / cap_real

    asc_real = CHINESE_FONT.ascent / CHINESE_FONT.upm
    CHINESE_SHIFT = (asc_real - 0.88) * size


def is_cjk(char):
    char = ord(char)
    if 0x2460 <= char <= 0x24FF:
        return True
    if 0x3000 <= char <= 0x318F:
        return True
    if 0x3200 <= char <= 0x32FF:
        return True
    if 0x3400 <= char <= 0x34BF:
        return True
    if 0x4E00 <= char <= 0x9FFF:
        return True
    if 0xAC00 <= char <= 0xD7AF:
        return True
    if 0xF900 <= char <= 0xFAFF:
        return True
    if 0x20000 <= char <= 0x2FFFF:
        return True
    return False


class CharClass(Enum):
    # 用西文字体
    WESTERN = 0
    # 用中文字体
    IDEOGRAPHIC = 1
    # 用系统自带符号字体
    LEFT_PUNCT = 2
    RIGHT_PUNCT = 3
    MID_PUNCT = 4
    COMMAS = 5
    PERIODS = 6
    LONG_PUNCT = 7
    OTHER_PUNCT = 8
    MATH_OP = 8
    MATH_REL = 9

    HALF_WIDTHS = [LEFT_PUNCT, RIGHT_PUNCT, MID_PUNCT, COMMAS, PERIODS]

    @classmethod
    def get_class(cls, char):
        if char in '([{‘“〔〈《「『【〖':
            return cls.LEFT_PUNCT  # 左括号
        if char in ')]}’”〕〉》」』】〗':
            return cls.RIGHT_PUNCT  # 右括号
        if char == '・':
            return cls.MID_PUNCT  # 中点（左右加空）
        if char in ',:;、':
            return cls.COMMAS  # 句中标点
        if char in '!.?。':
            return cls.PERIODS  # 句末标点
        if char in '—…':
            return cls.LONG_PUNCT  # 长标点
        if char in '‐–':
            return cls.OTHER_PUNCT  # 短横线
        if char in '+−±×÷∓':
            return cls.MATH_OP  # 数学运算符
        if char in '<=>≠≒≈≡≢≤≥≪	≫∧∨⊂⊃⊄⊅⊆⊇⊊⊋∈∋∉∪∩∥∦⇒⇔↔∽≌∝⊥⊕⊗':
            return cls.MATH_REL  # 数学关系符
        if is_cjk(char):
            return cls.IDEOGRAPHIC
        return cls.WESTERN


class Glyph:
    def __init__(self, code):
        self.cclass = CharClass.get_class(chr(code))
        self.font = 0
        self.code = code
        self.yshift = 0
        self.width = CHINESE_FONT_SIZE

        if self.cclass == CharClass.WESTERN:
            self.code = WESTERN_FONT.get_gid(code)
            self.font = get_font_encoding(WESTERN_FONT, WESTERN_FONT_SIZE)
            self.width = WESTERN_FONT_SIZE * WESTERN_FONT.get_glyph_width(self.code)
        elif self.cclass == CharClass.IDEOGRAPHIC:
            self.yshift = CHINESE_SHIFT
            self.code = CHINESE_FONT.get_gid(code)
            self.font = get_font_encoding(CHINESE_FONT, CHINESE_FONT_SIZE)
        elif self.cclass in CharClass.HALF_WIDTHS:
            self.width /= 2


class Glue:
    def __init__(self, default, plus, plus_priority, minus, minus_priority, allow_linebreak):
        self.default = default
        self.plus = plus
        self.plus_priority = plus_priority
        self.minus = minus
        self.minus_priority = minus_priority
        self.allow_linebreak = allow_linebreak


class HorElementType(Enum):
    DEFAULT = 0
    GLYPH = 1
    SPACE = 2
    HBOX = 3


class HBox:
    def __init__(self, t, content):
        self.type = t
        if t == HorElementType.GLYPH:
            self.content = Glyph(content)
        else:
            self.content = content


class TokenIterator:
    def __init__(self, token_list):
        self.token_list = token_list
        self.end = len(self.token_list)
        self.i = 0

    def has_next(self):
        return self.i < self.end

    def next_token(self):
        self.i += 1
        return self.token_list[self.i - 1]

    def skip(self, step):
        self.i += step


def process_token(token_list):
    # 初始化字体
    set_chinese_font(get_default_chinese_font())
    set_western_font(get_default_western_font())

    iterator = TokenIterator(token_list)
    paragraph_vlist = []

    current_hlist = []

    while iterator.has_next():
        cur_token = iterator.next_token()
        if cur_token.category == TokenType.CHAR:
            current_hlist.append(HBox(HorElementType.GLYPH, cur_token.content))
            pass
    return current_hlist
