from enum import Enum


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

    def get_class(self, char):
        if char in '([{‘“〔〈《「『【〖':
            return self.LEFT_PUNCT  # 左括号
        if char in ')]}’”〕〉》」』】〗':
            return self.RIGHT_PUNCT  # 右括号
        if char == '・':
            return self.MID_PUNCT  # 中点（左右加空）
        if char in ',:;、':
            return self.COMMAS  # 句中标点
        if char in '!.?。':
            return self.PERIODS  # 句末标点
        if char in '—…':
            return self.LONG_PUNCT  # 长标点
        if char in '‐–':
            return self.OTHER_PUNCT  # 短横线
        if char in '+−±×÷∓':
            return self.MATH_OP  # 数学运算符
        if char in '<=>≠≒≈≡≢≤≥≪	≫∧∨⊂⊃⊄⊅⊆⊇⊊⊋∈∋∉∪∩∥∦⇒⇔↔∽≌∝⊥⊕⊗':
            return self.MATH_REL  # 数学关系符
        if is_cjk(char)
            return self.IDEOGRAPHIC
        return self.WESTERN


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
    iterator = TokenIterator(token_list)
    paragraph_vlist = []

    while iterator.has_next():
        cur_token = iterator.next_token()
