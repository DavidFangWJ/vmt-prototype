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


allow_numeric_param = ['标题']
allow_length_param = ['字号']
NAN = float('nan')


def is_white_space(char):
    return char == ' ' or char == '\t'


# 生成一个Token列表.
def get_token_list(input_str):
    NEW_PARAGRAPH = Token(TokenType.NEW_PARAGRAPH, 0)

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
                    pass
                elif compressed_index in allow_length_param:  # 读取长度
                    pass
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
