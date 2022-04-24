from enum import Enum

from typing import List

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
        if char in '<=>≠≒≈≡≢≤≥≪≫∧∨⊂⊃⊄⊅⊆⊇⊊⊋∈∋∉∪∩∥∦⇒⇔↔∽≌∝⊥⊕⊗':
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
        elif self.cclass in [CharClass.LEFT_PUNCT, CharClass.RIGHT_PUNCT, CharClass.MID_PUNCT,
                             CharClass.COMMAS, CharClass.PERIODS]:
            self.width /= 2


class Glue:
    def __init__(self, default, plus, plus_priority, minus, minus_priority, end_width,
                 allow_linebreak):
        self.default = default
        self.plus = plus
        self.plus_priority = plus_priority
        self.minus = minus
        self.minus_priority = minus_priority
        self.end_width = end_width
        self.allow_linebreak = allow_linebreak

    def __repr__(self):
        return "{%f plus<%d> %f minus<%d> %f, end width %f, %s}" %\
               (self.default, self.plus_priority, self.plus, self.minus_priority, self.minus,
                self.end_width, self.allow_linebreak)


class HorElementType(Enum):
    DEFAULT = 0
    GLYPH = 1
    SPACE = 2
    HBOX = 3


class HBox:
    def __init__(self, t: HorElementType, content):
        self.type = t
        if t == HorElementType.GLYPH:
            self.content = Glyph(content)
        elif t == HorElementType.SPACE:
            self.content = Glue(content[0], content[1], content[2], content[3],
                                content[4], content[5], content[6])
        else:
            self.content = content

    def __repr__(self):
        if self.type == HorElementType.GLYPH:
            return "{Glyph, %d}" % self.content.code
        elif self.type == HorElementType.SPACE:
            return "{Glue, %s}" % self.content.__repr__()


def append_glue_to(hlist: List[HBox], glue_arg: List):
    hlist.append(HBox(HorElementType.SPACE, glue_arg))


def adjust_glue(hlist: List[HBox]):
    # 在最后两个字符间增加合适的空格量。一般来说没有空格就无法在此处换行。
    if len(hlist) < 2:
        return
    second_last = hlist[-2]
    if second_last.type != HorElementType.GLYPH:  # 不是字符
        return
    last = hlist[-1]
    hlist = hlist[:-1]
    if second_last.content.cclass == CharClass.MID_PUNCT:  # 中点之后
        glue_width = second_last.content.width  # 两个都是中点
        if last.content.cclass == CharClass.MID_PUNCT:
            glue_width += last.content.width
        glue_width /= 2
        append_glue_to(hlist, [glue_width, 0.0, 0, glue_width, 2, second_last.content.width, True])
    elif last.content.cclass == CharClass.MID_PUNCT:  # 中点之前
        glue_width = last.content.width / 2
        if second_last.content.cclass == CharClass.COMMAS:  # 逗号加中点
            append_glue_to(hlist, [second_last.content.width, 0.0, 0, second_last.content.width, 3,
                                   second_last.content.width, False])
        elif second_last.content.cclass == CharClass.PERIODS:  # 句号加中点
            append_glue_to(hlist, [second_last.content.width, 0.0, 0, 0.0, 0,
                                   second_last.content.width, False])
        append_glue_to(hlist, [glue_width, 0.0, 0, glue_width, 2, 0.0, False])
    elif second_last.content.cclass in [CharClass.RIGHT_PUNCT, CharClass.COMMAS]:  # 右标点之后
        if last.content.cclass not in [CharClass.RIGHT_PUNCT, CharClass.COMMAS, CharClass.PERIODS]:
            append_glue_to(hlist, [second_last.content.width, 0.0, 0, second_last.content.width, 3,
                                   second_last.content.width, True])
    elif second_last.content.cclass == CharClass.PERIODS:  # 句号
        if last.content.cclass not in [CharClass.RIGHT_PUNCT, CharClass.COMMAS, CharClass.PERIODS]:
            append_glue_to(hlist, [second_last.content.width, 0.0, 0, 0.0, 0,
                                   second_last.content.width, True])
    elif last.content.cclass == CharClass.LEFT_PUNCT:  # 左标点
        append_glue_to(hlist, [last.content.width, 0.0, 0, last.content.width, 3, 0.0, True])
    # 汉字和西文间
    elif second_last.content.cclass == CharClass.IDEOGRAPHIC\
            and last.content.cclass == CharClass.WESTERN:
        base_width = second_last.content.width / 4
        append_glue_to(hlist, [base_width, base_width, 2, base_width / 2, 4, 0.0, True])
    elif second_last.content.cclass == CharClass.WESTERN\
            and last.content.cclass == CharClass.IDEOGRAPHIC:
        base_width = last.content.width / 4
        append_glue_to(hlist, [base_width, base_width, 2, base_width / 2, 4, 0.0, True])
    # 汉字和汉字间
    elif second_last.content.cclass == CharClass.IDEOGRAPHIC\
            and last.content.cclass == CharClass.IDEOGRAPHIC:
        append_glue_to(hlist, [0.0, second_last.content.width / 4, 3, 0.0, 0, 0.0, True])
    hlist.append(last)
    pass


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
    set_font_size(3.75)

    iterator = TokenIterator(token_list)
    paragraph_vlist = []

    current_hlist = []
    western_temp_list = []

    while iterator.has_next():
        cur_token = iterator.next_token()
        if cur_token.category == TokenType.CHAR:
            hbox_glyph = HBox(HorElementType.GLYPH, cur_token.content)
            if hbox_glyph.content.cclass == CharClass.WESTERN:  # 西文字符特别处理
                western_temp_list.append(hbox_glyph)
            else:
                current_hlist.append(hbox_glyph)
                adjust_glue(current_hlist)
            pass
    return current_hlist
