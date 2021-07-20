from file_reader import read_file
from tokenizer import get_token_list
from font_library import Font, FontLibrary


if __name__ == '__main__':
    file_str = read_file('test.txt')

    token_list = get_token_list(file_str)

    font_library = FontLibrary()
    font_library.get_font('Noto Serif CJK SC')
    pass
