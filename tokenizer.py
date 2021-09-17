import sys
from enum import Enum


class TokenType(Enum):
    DEFAULT = 0
    CHAR = 1
    COMMAND = 2
    BEGIN_OF_GROUP = 3
    END_OF_GROUP = 4
    NUMBER = 5
    LENGTH = 6
    SPACE = 7
    NEW_PARAGRAPH = 8
    END_OF_FILE = 127

    def __repr__(self):
        if self == self.CHAR:
            return 'Character'
        if self == self.COMMAND:
            return 'Command'
        if self == self.BEGIN_OF_GROUP:
            return 'Begin of Group'
        if self == self.END_OF_GROUP:
            return 'End of Group'
        if self == self.NUMBER:
            return 'Number'
        if self == self.LENGTH:
            return 'Length'
        if self == self.SPACE:
            return 'Space'
        if self == self.NEW_PARAGRAPH:
            return 'New Paragraph'
        if self == self.END_OF_FILE:
            return 'End of File'


class Token:
    def __init__(self, category, content):
        self.category = category
        self.content = content

    def __repr__(self):
        if self.category == TokenType.CHAR:
            return '{Character, ' + chr(self.content) + '}'
        elif self.category == TokenType.NUMBER:
            return '{' + self.category.__repr__() + ', ' + '%.4f' % self.content + '}'
        elif self.category == TokenType.LENGTH:
            return '{' + self.category.__repr__() + ', ' + '%.4f' % self.content + ' mm}'
        elif self.category in [TokenType.COMMAND, TokenType.BEGIN_OF_GROUP, TokenType.END_OF_GROUP]:
            return '{' + self.category.__repr__() + ', ' + chr(self.content // 65536) + chr(self.content % 65536) + '}'
        else:
            return '{' + self.category.__repr__() + '}'


class TokenizerState(Enum):
    BEGIN_OF_LINE = 0
    MIDLINE = 1
    AFTER_SPACE = 2

    # 只用于命令和环境开头。不用于环境结尾。
    SKIP_EOC = 7


class StringReader:
    def __init__(self, input_str):
        self.string = input_str
        self.end = len(input_str)
        self.i = 0

    def has_next(self):
        return self.i < self.end

    def has_num_char(self, i):
        return self.i + i <= self.end

    def eat(self):
        self.i += 1
        return self.string[self.i - 1]

    def skip(self, step):
        self.i += step

    def read_number(self):
        start_pos = self.i
        allow_decimal = True
        while self.has_next():
            cur = self.eat()
            if cur == '.':
                if allow_decimal:
                    allow_decimal = False
                else:
                    self.skip(-1)
                    break
            elif cur not in '0123456789':
                self.skip(-1)
                break
        section = self.string[start_pos:self.i]
        return float(section)


allow_numeric_param = [
    0x68079898  # 标题
]
allow_length_param = [
    0x5B5753F7 # 字号
]
NAN = float('nan')

MM_PER_Q = 0.25
MM_PER_POINT = 0.3514
MM_PER_MM = 1

OLD_FONT_SIZE = [
    14.7590,  # 初号
    9.6637,   # 一号
    7.3795,   # 二号
    5.5346,   # 三号
    4.8318,   # 四号
    3.6898,   # 五号
    2.7673,   # 六号
    1.8449,   # 七号
    1.3837,   # 八号
]

NEW_PARAGRAPH = Token(TokenType.NEW_PARAGRAPH, 0)


def is_white_space(char):
    return char == ' ' or char == '\t'


# 生成一个Token列表.
def get_token_list(input_str):
    state = TokenizerState.BEGIN_OF_LINE
    result = []
    reader = StringReader(input_str)
    while reader.has_next():
        cur_char = reader.eat()
        if state == TokenizerState.BEGIN_OF_LINE:
            while is_white_space(cur_char):
                cur_char = reader.eat()
            if cur_char == '\n':
                if result[-1] != NEW_PARAGRAPH:
                    result.append(NEW_PARAGRAPH)
            else:
                reader.skip(-1)
                state = TokenizerState.MIDLINE
        elif state == TokenizerState.MIDLINE:
            if is_white_space(cur_char):
                result.append(Token(TokenType.SPACE, 0))
                state = TokenizerState.AFTER_SPACE
            elif cur_char == '\n':
                state = TokenizerState.BEGIN_OF_LINE
            elif cur_char == '〚':
                compressed_index = ord(reader.eat()) * 65536
                compressed_index += ord(reader.eat())
                if compressed_index in allow_numeric_param:  # 读取数字
                    num = reader.read_number()
                    result.append(Token(TokenType.NUMBER, num))
                elif compressed_index in allow_length_param:  # 读取长度
                    num = reader.read_number()
                    pass  # 读取单位符号部分用
                    # 目前允许的单位符号：Q（级）、pt（点）、mm（毫米）；H（号）使用时会报错误信息
                    cur_char = reader.eat()
                    if cur_char == 'H':  # 号数制
                        print('号数制已经过时，且可能会在未来版本中淘汰，请换用点或级！', file=sys.stderr)
                        num = OLD_FONT_SIZE[int(num)]
                    elif cur_char == 'Q':  # 级数制
                        num *= MM_PER_Q
                    else:
                        if reader.has_next():
                            cur_char += reader.eat()
                        if cur_char == 'pt':
                            num *= MM_PER_POINT
                        elif cur_char == 'mm':
                            num *= MM_PER_MM
                        else:
                            print('长度 %.4f 没有带长度单位，默认为级数。' % num, file=sys.stderr)
                            num *= MM_PER_Q
                            reader.skip(-1 * len(cur_char))
                    result.append(Token(TokenType.LENGTH, num))
                cur_char = reader.eat()
                if cur_char == ']':
                    result.append(Token(TokenType.BEGIN_OF_GROUP, compressed_index))
                else:
                    if cur_char != '〛':
                        print('错误：缺命令结束符', file=sys.stderr)
                        reader.skip(-1)
                    result.append(Token(TokenType.COMMAND, compressed_index))
            elif cur_char == '[' and reader.has_num_char(3):
                compressed_index = ord(reader.eat()) * 65536
                compressed_index += ord(reader.eat())
                cur_char = reader.eat()
                if cur_char == '〛':
                    result.append(Token(TokenType.END_OF_GROUP, compressed_index))
                else:
                    result.append(Token(TokenType.CHAR, 0x5B))  # 左括号的ASCII
                    reader.skip(-3)
            else:
                result.append(Token(TokenType.CHAR, ord(cur_char)))
        elif state == TokenizerState.AFTER_SPACE:
            while is_white_space(cur_char):
                cur_char = reader.eat()
            if cur_char == '\n':
                state = TokenizerState.BEGIN_OF_LINE
            else:
                reader.skip(-1)
                state = TokenizerState.MIDLINE
    result.append(Token(TokenType.END_OF_FILE, 0))
    return result
