from typing import List
from item_type import ItemType, TokenNode


left_punc = '([{‘“〔〈《「『【〖（［｛'
right_punc = ')]}’”〕〉》」』】〗）］｝,:;、，：；!.?。！？'


def tokenize_cn(content: str) -> List[TokenNode]:
    content = content.replace('\n', ' ').lstrip()
    length = len(content) - 1
    result = [TokenNode(ItemType.STRING, content[0])]

    pos = 0
    while pos < length:
        pos += 1
        current_char = content[pos]
        if current_char in ' \t':
            continue
        if current_char in right_punc or result[-1].content[-1] in left_punc:
            result[-1].content += current_char
        else:
            result.append(TokenNode(ItemType.STRING, current_char))
    return result
