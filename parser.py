from typing import Tuple, List, Dict

from item_type import ItemType, TokenNode


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


def parse(tokens: List[TokenNode], original_text: str) -> TokenNode:
    pred_stack = [TokenNode(ItemType.END_OF_FILE, None)]
    offset = 0
    tree_root = TokenNode(ItemType.DOCUMENT, None)
    pred_stack.append(tree_root)

    while len(pred_stack) > 1:
        type_next = tokens[offset].type
        # 遇到简谱、五线谱和歌词就重新tokenize
        if type_next == ItemType.KEYWORD:
            if tokens[offset].content in ['简谱', '五线谱', '歌词中']:
                pass  # 将来要对相关部分重新tokenize

        # 先判断可不可以移出符号
        type_top = pred_stack[-1].type
        type_next = tokens[offset].type
        if type_top == type_next:
            pred_stack[-1].content = tokens[offset].content
            pred_stack.pop()
            offset += 1
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
        pred_stack.extend(old_top.content)
        old_top.content.reverse()

    return tree_root
