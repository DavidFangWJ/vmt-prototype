# 旧版的LR分析器，不再维护了。

from typing import List
from item_type import ItemType, TokenNode


class JianpuNote:
    # 音符：note为数字（1～7），octave为上下加点数目（正上，负下，零不加），underline为减时线数目
    # 休止符：note和octave都是零
    # 增时线：note为-1，octave和underline都是零
    def __init__(self, note, octave, underline):
        self.note = note
        self.octave = octave
        self.underline = underline

    def __repr__(self):
        return '{Note = %d, octave = %d, underline = %d}' % (self.note, self.octave, self.underline)


def tokenize(content: str) -> List[TokenNode]:
    length = len(content)
    result = []

    pos = 0
    while pos < length:
        current_char = content[pos]
        if current_char in '01234567':
            result.append(TokenNode(ItemType.JIANPU_NOTE, JianpuNote(int(current_char), 0, 0)))
            if pos == length - 1:
                break
            index = ';:,\'"`'.find(content[pos + 1])
            if index >= 0:
                if index < 3:
                    index = index - 4
                else:
                    index = index - 2
                result[-1].content.octave = index
                pos += 1
            if pos == length - 1:
                break
            index = '_=/\\'.find(content[pos + 1])
            if index >= 0:
                result[-1].content.underline = index
                pos += 1
        pos += 1
        pass

    return result
