from typing import Tuple, List, Dict

from item_type import ItemType, TokenNode
import parser_jianpu
import parser_staff
import parser_lyric


# 词典中每一项的键是栈顶-下一个字符的对，值是逆序存入的推导式右侧结果。
predict_table: Dict[Tuple[ItemType, ItemType], List[ItemType]] = {
    # 1
    (ItemType.DOCUMENT, ItemType.KEYWORD): [ItemType.DOCUMENT_SUFFIX, ItemType.CLAUSE],
    (ItemType.DOCUMENT, ItemType.IDENTIFIER): [ItemType.DOCUMENT_SUFFIX, ItemType.CLAUSE],
    # 2
    (ItemType.DOCUMENT_SUFFIX, ItemType.BRACE_RIGHT): [ItemType.EMPTY],
    (ItemType.DOCUMENT_SUFFIX, ItemType.END_OF_FILE): [ItemType.EMPTY],
    # 3
    (ItemType.DOCUMENT_SUFFIX, ItemType.END_OF_LINE):
        [ItemType.DOCUMENT_SUFFIX, ItemType.CLAUSE, ItemType.END_OF_LINE],
    # 4
    (ItemType.CLAUSE, ItemType.KEYWORD): [ItemType.LAYOUT_STAFF],
    # 5
    (ItemType.CLAUSE, ItemType.IDENTIFIER): [ItemType.ASSIGNMENT_LIST],
    # 6
    (ItemType.LAYOUT_STAFF, ItemType.KEYWORD):
        [ItemType.BRACE_RIGHT, ItemType.DOCUMENT, ItemType.BRACE_LEFT, ItemType.KEYWORD],
    # 7
    (ItemType.ASSIGNMENT_LIST, ItemType.IDENTIFIER):
        [ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.IDENTIFIER],
    # 8
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.EQ): [ItemType.RHS, ItemType.EQ],
    # 9
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.BRACE_LEFT): [ItemType.LIST_SUFFIX, ItemType.ITEM_SUFFIX],
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.BRACE_RIGHT): [ItemType.LIST_SUFFIX, ItemType.ITEM_SUFFIX],
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.COMMA): [ItemType.LIST_SUFFIX, ItemType.ITEM_SUFFIX],
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.END_OF_LINE): [ItemType.LIST_SUFFIX, ItemType.ITEM_SUFFIX],
    (ItemType.ASSIGNMENT_LIST_SUFFIX, ItemType.END_OF_FILE): [ItemType.LIST_SUFFIX, ItemType.ITEM_SUFFIX],
    # 10
    (ItemType.LIST_SUFFIX, ItemType.BRACE_RIGHT): [ItemType.EMPTY],
    (ItemType.LIST_SUFFIX, ItemType.END_OF_LINE): [ItemType.EMPTY],
    (ItemType.LIST_SUFFIX, ItemType.END_OF_FILE): [ItemType.EMPTY],
    # 11
    (ItemType.LIST_SUFFIX, ItemType.COMMA): [ItemType.LIST_SUFFIX, ItemType.ITEM, ItemType.COMMA],
    # 12-18
    (ItemType.RHS, ItemType.NUMBER): [ItemType.NUMBER],
    (ItemType.RHS, ItemType.DIMEN): [ItemType.DIMEN],
    (ItemType.RHS, ItemType.STRING): [ItemType.STRING],
    (ItemType.RHS, ItemType.JIANPU): [ItemType.JIANPU],
    (ItemType.RHS, ItemType.STAFF): [ItemType.STAFF],
    (ItemType.RHS, ItemType.LYRIC): [ItemType.LYRIC],
    (ItemType.RHS, ItemType.IDENTIFIER): [ItemType.IDENTIFIER],
    (ItemType.ITEM, ItemType.IDENTIFIER): [ItemType.ITEM_SUFFIX, ItemType.IDENTIFIER],
    # 19
    (ItemType.ITEM_SUFFIX, ItemType.BRACE_RIGHT): [ItemType.EMPTY],
    (ItemType.ITEM_SUFFIX, ItemType.COMMA): [ItemType.EMPTY],
    (ItemType.ITEM_SUFFIX, ItemType.END_OF_LINE): [ItemType.EMPTY],
    (ItemType.ITEM_SUFFIX, ItemType.END_OF_FILE): [ItemType.EMPTY],
    # 20
    (ItemType.ITEM_SUFFIX, ItemType.BRACE_LEFT):
        [ItemType.BRACE_RIGHT, ItemType.IDENTIFIER, ItemType.BRACE_LEFT]
}


global original_text


def match_brace_close(index: int, tokens: List[TokenNode]) -> int:
    depth = 1
    while depth > 0:
        index += 1
        if index == len(tokens):
            print('错误：括号未匹配')
            exit(1)
        current = tokens[index]
        if current.type == ItemType.BRACE_LEFT:
            depth += 1
        elif current.type == ItemType.BRACE_RIGHT:
            depth -= 1
    return index


def match_music(index: int, tokens: List[TokenNode], node_type: ItemType, function)\
        -> Tuple[TokenNode, int]:
    """
    已知前提条件：index的位置是关键词“简谱”或“五线谱”的下一个位置
    :param index:
    :param tokens:
    :param node_type:
    :param function:
    :return:
    """
    result = []
    # 第一个括号
    if tokens[index].type != ItemType.BRACE_LEFT:
        print('错误：关键字后应有括号')
        exit(1)
    end_point = match_brace_close(index + 1, tokens)
    tokens[end_point].type = ItemType.END_OF_FILE
    result.append(parse_impl(tokens[index + 1:end_point + 1]))
    index = end_point + 1
    if tokens[index].type != ItemType.BRACE_LEFT:
        print('错误：乐谱结构应有第二个组')
        exit(1)
    end_point = match_brace_close(index + 1, tokens)
    music_section = original_text[tokens[index].content + 1:tokens[end_point].content]
    result.append(function(music_section))
    result = TokenNode(node_type, result)
    return result, end_point + 1
    pass


def match_lyric(index: int, tokens: List[TokenNode], node_type: ItemType, function)\
        -> Tuple[TokenNode, int]:
    """
    已知前提条件：index的位置是关键词“歌词中”或“歌词英”的下一个位置
    :param index:
    :param tokens:
    :param node_type:
    :param function:
    :return:
    """
    # 第一个括号
    if tokens[index].type != ItemType.BRACE_LEFT:
        print('错误：关键字后应有括号')
        exit(1)
    end_point = match_brace_close(index + 1, tokens)
    lyric_section = original_text[tokens[index].content + 1:tokens[end_point].content]
    result = function(lyric_section)
    result = TokenNode(node_type, result)
    return result, end_point + 1
    pass


def parse(tokens: List[TokenNode], _original_text: str) -> TokenNode:
    global original_text
    original_text = _original_text

    return parse_impl(tokens)


def parse_impl(tokens: List[TokenNode]) -> TokenNode:
    pred_stack = [TokenNode(ItemType.END_OF_FILE, None)]
    offset = 0
    tree_root = TokenNode(ItemType.DOCUMENT, None)
    pred_stack.append(tree_root)

    str_to_type = {'简谱': (ItemType.JIANPU, parser_jianpu.tokenize),
                   '五线谱': (ItemType.STAFF, parser_staff.tokenize),
                   '歌词中': (ItemType.LYRIC, parser_lyric.tokenize_cn)}

    type_next = tokens[0].type
    while len(pred_stack) > 1:
        # 遇到简谱、五线谱和歌词就重新tokenize
        if type_next == ItemType.KEYWORD:
            if tokens[offset].content in ['简谱', '五线谱', '歌词中']:
                type_next, fun_next = str_to_type[tokens[offset].content]
                if tokens[offset].content[0] == '歌':
                    node, index = match_lyric(offset + 1, tokens, type_next, fun_next)
                else:
                    node, index = match_music(offset + 1, tokens, type_next, fun_next)
                tokens = [*tokens[:offset], node, *tokens[index:]]

        # 先判断可不可以移出符号
        type_top = pred_stack[-1].type
        if type_top == type_next:
            pred_stack[-1].content = tokens[offset].content
            pred_stack.pop()
            offset += 1
            type_next = tokens[offset].type
            continue
        # 如果栈顶的终结符不匹配，直接报错
        if type_top.is_terminal():
            print('需要 %s 类型，但相应的 Token 为 %s' % (type_top[9:], tokens[offset]))
            exit(1)

        if (type_top, type_next) not in predict_table.keys():
            print('代码语法有错误，但是报错部分还没写')
            exit(1)
        list_nodes = predict_table[(type_top, type_next)]
        old_top = pred_stack[-1]
        pred_stack.pop()
        old_top.content = []
        for i in list_nodes:
            old_top.content.append(TokenNode(i, None))
        if list_nodes[0] != ItemType.EMPTY:
            pred_stack.extend(old_top.content)
            old_top.content.reverse()

    return tree_root
