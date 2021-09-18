from file_reader import read_file
from tokenizer import get_token_list
from token_process import process_token
from global_var import initialize_font_library


if __name__ == '__main__':
    file_str = read_file('test.txt')

    token_list = get_token_list(file_str)

    initialize_font_library('思源宋体', 'FreeSerif')
    temp = process_token(token_list)
    pass
