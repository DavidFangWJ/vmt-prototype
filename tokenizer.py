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
            return "Character"
        if self == self.SPACE:
            return "Space"
        if self == self.NEW_PARAGRAPH:
            return "New Paragraph"
        if self == self.END_OF_FILE:
            return "End of File"


class Token:
    def __init__(self, category, content):
        self.category = category
        self.content = content

    def __repr__(self):
        if self.category == TokenType.CHAR:
            return '{' + self.category.__repr__() + ', ' + chr(self.content) + '}'
        else:
            return '{' + self.category.__repr__() + '}'


class TokenizerState(Enum):
    BEGIN_OF_LINE = 0
    MIDLINE = 1
    AFTER_SPACE = 2
    PREPARE_NUM = 3
    PREPARE_LEN = 4


def is_white_space(char):
    return char == ' ' or char == '\t'


# 生成一个Token列表.
def get_token_list(input_str):
    state = TokenizerState.BEGIN_OF_LINE
    result = []
    i = 0
    end = len(input_str)
    while i < end:
        cur_char = input_str[i]
        # 行首
        if state == TokenizerState.BEGIN_OF_LINE:
            if cur_char == '\n':
                if result[-1].category != TokenType.NEW_PARAGRAPH:
                    result.append(Token(TokenType.NEW_PARAGRAPH, 0))
                i += 1
                continue
            else:
                state = TokenizerState.AFTER_SPACE
        # 忽略回车
        if cur_char == '\n':
            state = TokenizerState.BEGIN_OF_LINE
            i += 1
            continue
        if state == TokenizerState.AFTER_SPACE:
            if is_white_space(cur_char):
                i += 1
                continue
            else:
                state = TokenizerState.MIDLINE
        # 多数情况下直接放入
        if state != TokenizerState.PREPARE_NUM and state != TokenizerState.PREPARE_LEN:
            if is_white_space(cur_char):
                result.append(Token(TokenType.SPACE, 0))
                state = TokenizerState.AFTER_SPACE
            elif cur_char == '〚':  # 段落开始
                if i + 3 >= end:  # 命令未结束
                    print('错误: 命令未正常结束')
                    break
                compressed_index = ord(input_str[i+1]) * 65536 + ord(input_str[i+2])
                if input_str[i+3] == '〛':  # 命令
                    result.append(Token(TokenType.COMMAND, compressed_index))
                    i += 2
                elif input_str[i+3] == ']':  # 环境始
                    result.append(Token(TokenType.BEGIN_OF_GROUP, compressed_index))
                    i += 2
                else:
                    print('错误: 命令未正常结束')
                    break
            elif cur_char == '[' and i + 3 < end and input_str[i+3] == '〛':  # 环境终
                result.append(Token(TokenType.END_OF_GROUP, ord(input_str[i+1]) * 65536 + ord(input_str[i+2])))
                i += 2
            else:
                result.append(Token(TokenType.CHAR, ord(cur_char)))
        i += 1
    result.append(Token(TokenType.END_OF_FILE, 0))
    return result
