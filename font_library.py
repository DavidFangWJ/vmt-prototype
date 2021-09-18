import sys
from ctypes import *
from struct import unpack


class Type4CmapTable:
    """
    4 型 cmap 表。
    """
    def __init__(self, in_file):
        in_file.seek(2, 1)
        length, double_seg_count = unpack('>HH', in_file.read(4))
        in_file.seek(6, 1)
        length -= 4 * double_seg_count + 16

        self.seg_count = double_seg_count // 2

        self.end_code = unpack('>' + 'H' * self.seg_count, in_file.read(double_seg_count))
        in_file.seek(2, 1)
        self.start_code = unpack('>' + 'H' * self.seg_count, in_file.read(double_seg_count))
        self.id_delta = unpack('>' + 'H' * self.seg_count, in_file.read(double_seg_count))
        self.id_range_offset = unpack('>' + 'H' * self.seg_count, in_file.read(double_seg_count))

        if length > 0:
            self.glyph_id_array = unpack('>' + 'H' * (length // 2), in_file.read(length))
        else:
            self.glyph_id_array = []

    def get_gid(self, uid):
        current_segment = 0
        while current_segment < self.seg_count:
            if self.end_code[current_segment] > uid:
                break
            current_segment += 1

        if current_segment == self.seg_count or self.start_code[current_segment] > uid:  # UID 不存在
            return 0

        if self.id_range_offset[current_segment] == 0:
            gid = uid + self.id_delta[current_segment]
        else:
            index = uid - self.start_code[current_segment]
            index += self.id_range_offset[current_segment] / 2 + current_segment - self.seg_count
            gid = self.glyph_id_array[index] + self.id_delta[current_segment]

        return gid % 65536


class Type12CmapTable:
    """
    12 型 cmap 表。
    """
    def __init__(self, in_file):
        in_file.seek(12, 1)
        self.num_group = unpack('>I', in_file.read(4))[0]
        self.start_code = []
        self.end_code = []
        self.start_gid = []

        for i in range(self.num_group):
            self.start_code.extend(unpack('>I', in_file.read(4)))
            self.end_code.extend(unpack('>I', in_file.read(4)))
            self.start_gid.extend(unpack('>I', in_file.read(4)))

    def get_gid(self, uid):
        current_segment = 0
        while current_segment < self.num_group:
            if self.end_code[current_segment] >= uid:
                break
            current_segment += 1

        if current_segment == self.num_group or self.start_code[current_segment] > uid:  # UID 不存在
            return 0

        return uid - self.start_code[current_segment] + self.start_gid[current_segment]


class Font:
    """
    表示字体的对象。因为 FontConfig 功能不足，不得不自己写。
    tables是一个字典，记录了字体中所有表的位置和长度。
    可以自己加入用于读取GSUB、GPOS、cmap、hmtx等表的数据结构。
    """

    def __init__(self, font_dir, index, is_western):
        """
        从目录生成字体（待完成）。
        :param font_dir: 字体所在的目录。
        :param index: 如果字体是 ttc，则表示所用字体的序号；否则无意义。
        :param is_western: 字体是否是西文字体。
        """
        self.font_file = open(font_dir, 'rb')
        self.tables = {}
        tag = self.font_file.read(4)
        if tag == b'ttcf':
            self.font_file.seek(8, 0)
            num_fonts = unpack('>I', self.font_file.read(4))[0]
            if num_fonts <= index:  # index超出了，强制置0
                print('要求 {} 号字体，但 TTC 内只有 {} 笔数据'.format(index, num_fonts), file=sys.stderr)
                index = 0
            self.font_file.seek(index * 4, 1)
            table_offset = unpack('>I', self.font_file.read(4))[0]
            self.font_file.seek(table_offset + 4, 0)
        num_tables = unpack('>HHL', self.font_file.read(8))[0]
        for i in range(num_tables):
            cur_table_raw = self.font_file.read(16)
            offset = unpack('>I', cur_table_raw[8:12])[0]
            self.tables[cur_table_raw[:4].decode()] = offset
        self.is_cid = self.__is_cid()

        self.__init_cmap_table()
        self.upm, self.ascent, self.caps_height = self.__get_typo_data()
        self.hmtx = self.__get_hmtx(is_western)  # 读取 hmtx 表

    def __del__(self):
        """
        析构字体。因为 Python 对象会自动析构，所以只用关闭字体文件。
        """
        self.font_file.close()

    def get_gid(self, uid):
        """
        从已有的 Unicode 编码值中得出 GID/CID。
        :param uid: Unicode编码值
        :return: 相应的 GID/CID。
        """
        return self.cmap.get_gid(uid)

    def get_glyph_width(self, gid):
        """
        计算某个字符的宽度，以 em 为单位。
        :param gid: 字符序号
        :return: 字符宽度，以 em 为单位，为此需要从 `head` 表读取 UPM。
        """
        if self.is_cid:  # 懒得读 CFF，暂时禁止用 CID 字体生成西文
            print('禁止用 CID 字体充当西文字体！', file=sys.stderr)
            return 1.0
        if gid > len(self.hmtx):
            width = self.hmtx[-1]
        else:
            width = self.hmtx[gid]
        return width / self.upm

    def process_gsub_liga(self, list_gids):
        """
        对一连串字符自动做连字处理。（待完成）
        :param list_gids: 一个整型列表，解析为 GID。
        """
        pass

    def get_kern(self, gid1, gid2):
        """
        计算任意两个字符间的 kerning 值。（待完成）
        :param gid1: 左侧字符
        :param gid2: 右侧字符
        :return: kerning值，以 em 表示。
        """
        return 0

    def __is_cid(self):
        """
        知道某个字体是不是 CID-keyed 的。
        :return: 布尔值，True 表示 CID-keyed，False 表示 name-keyed 或 ttf。
        """
        if 'CFF ' not in self.tables.keys():  # ttf
            return False
        cff_offset = self.tables['CFF ']

        self.font_file.seek(cff_offset + 2, 0)
        header_size = unpack('B', self.font_file.read(1))[0]
        self.font_file.seek(header_size + 1, 1)

        # 读取CFF字体名。OTF用的CFF子集中，Name Index只能包括一个名字，且一定是256字节以内，因此前四个字节一定是00010101
        name_length = unpack('B', self.font_file.read(1))[0] - 1

        # 确定是不是 CID 字体
        self.font_file.seek(name_length + 2, 1)
        index_int_size = unpack('B', self.font_file.read(1))[0]  # 偏移量长度
        self.font_file.seek(index_int_size * 2, 1)
        while True:
            cur = unpack('B', self.font_file.read(1))[0]
            if 32 <= cur <= 246:  # 单字节
                continue
            elif 247 <= cur <= 254:  # 双字节
                self.font_file.seek(1, 1)
            elif cur == 28:  # 三字节
                self.font_file.seek(2, 1)
            elif cur == 29:  # 五字节
                self.font_file.seek(4, 1)
            elif cur != 12:
                return False
            else:
                cur = unpack('B', self.font_file.read(1))[0]
                return cur == 30

    def __init_cmap_table(self):
        offset_cmap = self.tables['cmap']
        self.font_file.seek(offset_cmap + 2, 0)
        num_tables = unpack('>H', self.font_file.read(2))[0]

        records = []
        for i in range(num_tables):
            records.append(unpack('>II', self.font_file.read(8)))

        cmap_type = 0
        cmap_offset = 0

        for item in records:
            if item[0] == 0x030001:
                cmap_type = 4
                cmap_offset = item[1]
            elif item[0] == 0x03000A:
                cmap_type = 12
                cmap_offset = item[1]
            elif item[0] > 0x03000A:
                break
        offset_cmap += cmap_offset
        self.font_file.seek(offset_cmap, 0)

        if cmap_type == 4:
            self.cmap = Type4CmapTable(self.font_file)
        elif cmap_type == 12:
            self.cmap = Type12CmapTable(self.font_file)
        else:
            print('字体没有合适的cmap表。', file=sys.stderr)
            exit(1)

    def __get_typo_data(self):
        self.font_file.seek(self.tables['head'] + 18, 0)
        upm = unpack('>H', self.font_file.read(2))[0]
        self.font_file.seek(self.tables['OS/2'] + 68, 0)
        ascent = unpack('>h', self.font_file.read(2))[0]
        self.font_file.seek(18, 1)
        caps_height = unpack('>h', self.font_file.read(2))[0]
        return upm, ascent, caps_height

    def __get_hmtx(self, is_western):
        if is_western and not self.is_cid:
            result = []
            self.font_file.seek(self.tables['hhea'] + 34, 0)
            num_hmtx = unpack('>H', self.font_file.read(2))[0]
            self.font_file.seek(self.tables['hmtx'], 0)
            for i in range(num_hmtx):
                result.append(unpack('>HH', self.font_file.read(4))[0])
            return result
        else:
            return None


class FontLibrary:
    def __init__(self, chinese, western):
        self.lib = cdll.LoadLibrary('libfontconfig.so')
        self.config = self.lib.FcInitLoadConfigAndFonts()

        self.font_dict = {}
        self.default_chinese = self.get_font(chinese, False)
        self.default_western = self.get_font(western, True)

    def get_font(self, font_name, is_western):
        """
        根据字体名查找字体。
        :param font_name: 字体名。
        :param is_western: 是否为西文字体（需要 `hmtx` 表）
        :return: 相应的font对象。
        """
        if font_name in self.font_dict:
            return self.font_dict[font_name]

        # 用fcconfig找到字体位置
        font_dir, index = self.__get_font_dir(font_name)
        new_font = Font(font_dir, index, is_western)
        self.font_dict[font_name] = new_font
        return new_font

    def __get_font_dir(self, font_name):
        font_name_cstr = c_char_p(str.encode(font_name))
        pat = self.lib.FcNameParse(font_name_cstr)
        self.lib.FcConfigSubstitute(self.config, pat, 0)
        self.lib.FcDefaultSubstitute(pat)

        res = c_uint32()
        direc = c_char_p()
        index = c_int32()

        font = self.lib.FcFontMatch(self.config, pat, byref(res))
        if font == c_void_p():
            print('字体“{}”不存在。'.format(font_name), file=sys.stderr)
            exit(1)
        if self.lib.FcPatternGetString(font, b'file', 0, byref(direc)) != 0:
            print('fontconfig 出现未知错误', file=sys.stderr)
            exit(1)
        if self.lib.FcPatternGetInteger(font, b'index', 0, byref(index)) != 0:
            index.value = 0

        font_dir = direc.value.decode()

        self.lib.FcPatternDestroy(font)
        self.lib.FcPatternDestroy(pat)
        return font_dir, index.value
