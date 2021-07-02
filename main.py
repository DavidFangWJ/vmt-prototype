from file_reader import read_file
from tokenizer import get_token_list


if __name__ == '__main__':
    file_str = read_file('test.txt')

    token_list = get_token_list(file_str)
    for token in token_list:
        print(token)
