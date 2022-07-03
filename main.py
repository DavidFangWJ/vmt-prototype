from tokenizer import tokenize
from parser import parse


if __name__ == '__main__':
    f = open('preview.txt', 'r')
    content = f.read()
    tokens = tokenize(content)
    parse_tree = parse(tokens, content)
    pass
