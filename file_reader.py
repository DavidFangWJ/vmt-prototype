def normalize(string):
    # 全半角问题
    string = string.replace('　', '').replace('·', '・').replace('～', '〜')
    for i in range(33, 128):
        string = string.replace(chr(i - 32 + 0xFF00), chr(i))
    return string


def read_file(filename):
    f = open(filename, 'r')
    file_str = f.read()
    f.close()
    return normalize(file_str)
