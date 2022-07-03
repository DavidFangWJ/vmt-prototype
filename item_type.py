from enum import Enum


class ItemType(Enum):
    # 终结符
    IDENTIFIER = 0  # 标识符
    KEYWORD = 1  # 关键字
    NUMBER = 2  # 数字
    DIMEN = 3  # 长度
    STRING = 4  # 字符串
    BRACE_LEFT = 5  # 左大括号
    BRACE_RIGHT = 6  # 右大括号
    EQ = 7  # 赋值符号
    END_OF_LINE = 8  # 行尾
    COMMA = 9  # 逗号
    END_OF_FILE = 10  # 文档结束
    # 特殊的终结符
    JIANPU = 11
    STAFF = 12
    LYRIC = 13
    EMPTY = 14
    # 非终结符
    DOCUMENT = 15
    DOCUMENT_SUFFIX = 16
    CLAUSE = 17
    LAYOUT_STAFF = 18
    ASSIGNMENT_LIST = 19
    ASSIGNMENT_LIST_SUFFIX = 20
    LIST_SUFFIX = 21
    RHS = 22
    ITEM = 23
    ITEM_SUFFIX = 24

    def is_terminal(self) -> bool:
        return self.value < self.DOCUMENT.value


class TokenNode:
    def __init__(self, token_type: ItemType, content):
        self.type = token_type
        self.content = content

    def __repr__(self):
        return "{%s, %s}" % (str(self.type)[9:], str(self.content))
