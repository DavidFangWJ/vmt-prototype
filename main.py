from file_reader import read_file
from tokenizer import get_token_list
from font_library import Font, FontLibrary


if __name__ == '__main__':
    file_str = read_file('test.txt')

    token_list = get_token_list(file_str)

    font_library = FontLibrary()
    free_serif = font_library.get_font('FreeSerif', True)
    print(free_serif.get_glyph_width(3))
    pass
