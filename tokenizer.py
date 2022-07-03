import re
from enum import Enum
from typing import List
from item_type import ItemType, TokenNode


# unit_factor = {'mm': 1.0, 'cm': 10.0, 'pt': 0.3514}


def generate_token(content: str) -> TokenNode:
    # list_of_keywords = ['版面', '宽度', '音符字号', '歌词字号', '字体', '每拍宽度', '简谱', '五线谱', '谱表']
    list_of_keywords = ['版面', '简谱', '五线谱', '歌词中', '谱表']
    if content in list_of_keywords:
        return TokenNode(ItemType.KEYWORD, content)

    match = re.match(r'\d+(\.\d*)?', content)
    if match:
        number = float(match.group(0))
        remainder = content[match.end():]
        if re.fullmatch(r'[A-Za-z]+', remainder):
            # print('不合法单位：%s，默认视为毫米。' % remainder)
            return TokenNode(ItemType.DIMEN, (number, remainder))
        elif len(remainder) == 0:
            return TokenNode(ItemType.NUMBER, number)

    return TokenNode(ItemType.IDENTIFIER, content)


def tokenize(content: str) -> List[TokenNode]:
    length = len(content)
    result = []
    current = ''

    pos = 0
    while pos < length:
        current_char = content[pos]
        if current_char in ' \t\n;={},"' and len(current) > 0:
            result.append(generate_token(current))
            current = ''
        while current_char in ' \t':
            pos += 1
            current_char = content[pos]
        if current_char == '%':
            while current_char != '\n':
                pos += 1
                current_char = content[pos]
        elif current_char == '=':
            result.append(TokenNode(ItemType.EQ, None))
        elif current_char == '{':
            result.append(TokenNode(ItemType.BRACE_LEFT, pos))
        elif current_char == '}':
            if result[-1].type == ItemType.END_OF_LINE:
                result.pop()
            result.append(TokenNode(ItemType.BRACE_RIGHT, pos))
        elif current_char == '\n' or current_char == ';':
            if len(result) > 0 and result[-1].type != ItemType.END_OF_LINE\
                    and result[-1].type != ItemType.BRACE_LEFT:
                result.append(TokenNode(ItemType.END_OF_LINE, pos))
        elif current_char == ',':
            result.append(TokenNode(ItemType.COMMA, None))
        elif current_char == '"':
            pos += 1
            current_char = content[pos]
            while current_char != '"':
                current += current_char
                pos += 1
                if pos == len(content):
                    print("字符串双引号不匹配")
                    exit(1)
                current_char = content[pos]
                pass
            result.append(TokenNode(ItemType.STRING, current))
            current = ''
        else:
            current += current_char
        pos += 1

    while result[-1].type == ItemType.END_OF_LINE:
        result.pop()
    result.append(TokenNode(ItemType.END_OF_FILE, None))

    return result
