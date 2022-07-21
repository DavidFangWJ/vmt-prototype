from typing import List
from item_type import ItemType, TokenNode


class StaffNote:
    def __init__(self, note: str, accidental: int, octave: int, length: int):
        self.note = note
        self.accidental = accidental
        self.octave = octave
        self.length = length

    def __repr__(self):
        accidental = octave = ''
        if self.accidental > 0:
            accidental = 'is' * self.accidental
        elif self.accidental < 0:
            accidental = 'es' * -self.accidental
        if self.octave > 0:
            octave = '\'' * self.octave
        elif self.octave < 0:
            octave = ',' * -self.octave
        return '%c%s%s%d' % (self.note, accidental, octave, self.length)


def calc_octave(old_note: StaffNote, new_name: str) -> int:
    difference = ord(old_note.note) - ord(new_name)
    result = old_note.octave + int((difference + 3.5) // 7.0)
    if new_name in 'ab':
        result -= 1
    return result


def tokenize(content: str) -> List[TokenNode]:
    length = len(content)
    result = [TokenNode(ItemType.STAFF_NOTE, StaffNote('f', 0, 0, 0))]

    pos = 0
    while pos < length:
        current_char = content[pos]
        # 顺序：音名-变音记号-增减八度-时值
        if current_char in 'abcdefg':
            result.append(TokenNode(ItemType.STAFF_NOTE,
                                    StaffNote(current_char, 0,
                                              calc_octave(result[-1].content, current_char),
                                              result[-1].content.length)))
            if pos == length - 1:
                break
            pos += 1
            # 升号及重升号
            if pos + 4 < length and content[pos:pos + 4] == 'isis':
                result[-1].content.accidental = 2
                pos += 4
            elif pos + 2 < length and content[pos:pos + 2] == 'is':
                result[-1].content.accidental = 1
                pos += 2
            # 降号及重降号
            elif (pos + 2 < length and content[pos:pos + 2] == 'es')\
                    or (pos < length and result[-1].content.note in 'ae' and content[pos] == 's'):
                result[-1].content.accidental = -1
                if content[pos] == 's':
                    pos += 1
                else:
                    pos += 2
                if content[pos:pos+2] == 'es':
                    result[-1].content.accidental = -2
                    pos += 2
            # 八度增减
            if pos < length and content[pos] == '\'':
                result[-1].content.octave += 1
                pos += 1
                while pos < length and content[pos] == '\'':
                    result[-1].content.octave += 1
                    pos += 1
            elif pos < length and content[pos] == ',':
                result[-1].content.octave -= 1
                pos -= 1
                while pos < length and content[pos] == ',':
                    result[-1].content.octave -= 1
                    pos += 1
            if pos < length and content[pos] in '0123456789':
                tmp = content[pos]
                pos += 1
                while pos < length and content[pos] in '0123456789':
                    tmp += content[pos]
                    pos += 1
                result[-1].content.length = int(tmp)
        pos += 1
        pass

    return result[1:]
