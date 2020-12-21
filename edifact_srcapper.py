import argparse
import re
import requests
import time
from bs4 import BeautifulSoup

#TODO start
# Adding Data Element Cross Reference?
# Add Note Attribute to Data Element? (only appears in some data elments ex:3229)
#TODO end

base_URL = 'https://service.unece.org/trade/untdid/'
verbose = False
verbose_text = ''

class Item():
    def __init__(self, tag, name, function):
        self.tag = tag
        self.name = name
        self.function = function

class Segment(Item):
    def __init__(self, tag, name, function, data_elements, used_in_messages, url):
        super().__init__(tag, name, function)
        self.data_elements = data_elements
        self.used_in_messages = used_in_messages
        self.url = url
    def info(self):
        print('tag: {}'.format(self.tag))
        print('name: {}'.format(self.name))
        print('function: {}'.format(self.function))
        print('url: {}'.format(self.url))
        print('data elements:')
        for data_element in self.data_elements:
            print('{}|{}|{}'.format(data_element[0], data_element[1], data_element[2]))
        print('used in messages:')
        for message in self.used_in_messages:
            print('{}|'.format(message), end='')
        print()

class Composite_data_element(Item):
    def __init__(self, tag, name, function, data_elements, used_in_segments, url):
        super().__init__(tag, name, function)
        self.data_elements = data_elements
        self.used_in_segments = used_in_segments
        self.url = url

    def info(self):
        print('tag: {}'.format(self.tag))
        print('name: {}'.format(self.name))
        print('function: {}'.format(self.function))
        print('url: {}'.format(self.url))
        print('data elements:')
        for data_element in self.data_elements:
            print('{}|{}|{}'.format(data_element[0], data_element[1], data_element[2]))
        print('used in segments:')
        for segment in self.used_in_segments:
            print('{}|'.format(segment), end='')
        print()

class Data_element(Item):
    def __init__(self, tag, name, function, format, code_list, url):
    # def __init__(self, tag, name, function, format, code_list, used_in_batch_seg,
    #              used_in_batch_composite, used_in_interactive_seg, used_in_interactive_composite):
        super().__init__(tag, name, function)
        self.format = format
        self.code_list = code_list
        self.url = url
        #self.used_in_batch_seg = used_in_batch_seg
        #self.used_in_batch_composite = used_in_batch_composite
        #self.used_in_interactive_seg = used_in_interactive_seg
        #self.used_in_interactive_composite = used_in_interactive_composite

    def info(self):
        print('tag: {}'.format(self.tag))
        print('name: {}'.format(self.name))
        print('function: {}'.format(self.function))
        print('format: {}'.format(self.format))
        print('url: {}'.format(self.url))
        print('codes:')
        for code in self.code_list:
            print('{}|{}|{}'.format(code.value, code.name, code.description))
        # print('used in messages:')
        # for segment in self.used_in_batch_seg:
        #     print('{}|'.format(segment), end='')
        # for composite in self.used_in_batch_composite:
        #     print('{}|'.format(composite), end='')
        # for segment in self.used_in_interactive_seg:
        #     print('{}|'.format(segment), end='')
        # for composite in self.used_in_interactive_composite:
        #     print('{}|'.format(composite), end='')
        print()

class CodeItem():
    def __init__(self, value, name, description):

        self.value = value
        self.name = name
        self.description = description

class Dir():
    def __init__(self, version, mode, url):
        self.version = version
        self.mode = mode
        self.url = url

class Segment_Dir(Dir):
    def __init__(self, version, mode, url, segments):
        super().__init__(version, mode, url)
        self.segments = segments

class Composite_Dir(Dir):
    def __init__(self, version, mode, url, composite_elements):
        super().__init__(version, mode, url)
        self.segments = composite_elements

class Element_Dir(Dir):
    def __init__(self, version, mode, url, data_elements):
        super().__init__(version, mode, url)
        self.segments = data_elements

def check_version_type(version, pat=re.compile(r"^[dD][0-9]{2}[abAB]$")):
    """check if syntactically valid EDIFACT version."""
    error = 'Invalid EDIFACT release version: {}'.format(version)
    if not pat.match(version) and __name__ == "__main__":
        raise argparse.ArgumentTypeError(error)
    elif not pat.match(version):
        raise ValueError(error)
    return version

def check_mode_type(mode):
    """check if EDIFACT mode is 'tr' (batch) or 'ti' (interactive) and translate to code."""
    error = 'Invalid EDIFACT mode: {} (allowed: tr (batch) or ti (interactive)'.format(mode)
    if mode != 'tr' and mode != 'ti' and __name__ == "__main__":
         raise argparse.ArgumentTypeError(error)
    if mode != 'tr' and mode != 'ti':
         raise ValueError(error)
    return mode

def get_page_from_URL(URL):
    """ request URL and try again if it fails. Print result if verbose is on."""
    page = None
    while page is None:
        try:
            page = requests.get(URL)
            if verbose: print('OK')
        except:
            if verbose: print('Oops! ... trying again ...', end = '')
    return page

def get_tags_from_website(mode, version, type):
    """to scrap service.unece.org for EDIFACT segment tags.
       arguments: mode, version
       mode: tr (batch), ti (interactive)
       version: EDIFACT version (ex. d96a)
       type: which kind of tags?
            segments: sd, composite data elements: cd, simple_data_element: ed
       returns a list containing all tags"""
    global verbose_text
    tags = list()
    check_mode_type(mode)
    check_version_type(version)
    URL = base_URL + version.lower() + '/' + mode + type + '/' + mode + type + 'i1.htm'

    if verbose: print('Let\'s go!')
    if verbose: print('Scrap service.unece.org for EDIFACT segments and returning a list of all tags.')
    if verbose: print('...from {} ...getting tag-list: - '.format(URL), end = '')
    page = get_page_from_URL(URL)

    if page is not None:
        soup = BeautifulSoup(page.content, 'html.parser')
        links = soup.find_all("a")

        for link in links:
            if type == 'sd' and len(link.text) == 3:
                tags.append(link.text)
            if type == 'cd' and len(link.text) == 4 and link.text.startswith('C'):
                tags.append(link.text)
            if type == 'ed' and len(link.text) == 4 and link.text.isdigit():
                tags.append(link.text)
        if verbose: print('Extracted total tags: {}'.format(len(tags)))
    return tags

def create_item(mode, version, tag, type):
    URL = base_URL + version.lower() + '/' + mode + type + '/' + mode + type + tag.lower() + '.htm'
    if verbose: print('...from {} ...getting tag: {} - '.format(URL, tag), end = '')

    page = get_page_from_URL(URL)
    if page is not None:
        soup = BeautifulSoup(page.content, 'html.parser')

        if type == 'ed':
            item = get_data_element_from_soup(soup, type, URL)
        else:
            item = get_item_from_soup(soup, type, URL)
        return item
    else:
        return None

def create_item_list(mode, version, tags, type):
    """to create and return a list of segment, composite or data_element objects."""
    global verbose_text

    check_mode_type(mode)
    check_version_type(version)
    if verbose: print('Getting all single tags from their URL.')
    items = []
    for tag in tags:
        items.append(create_item(mode, version, tag, type))
    if verbose: print('Build {} items of type {}-structures out of {} tags.'.format(len(items), type, len(tags)))
    if verbose and len(items) == len(tags): print('Looks good!')

    return items

def get_item_from_soup(soup, type, url):
    """to scrap edifact directory pages (sd, cd) (ex. https://service.unece.org/trade/untdid/d19a/trsd/trsdbgm.htm)
       build and return a segment, composite or data element object."""
    #extract tag and name
    tag_name = soup.find("h3")

    if tag_name.text.lstrip().startswith('X') or tag_name.text.lstrip().startswith('-'):
        tag_name_tmp = tag_name.text.lstrip()[3:]
    else:
        tag_name_tmp = tag_name.text

    if type == 'sd':
        tag = tag_name_tmp.lstrip()[:3]
        name = tag_name_tmp.lstrip()[3:].lstrip()
    elif type == 'cd':
        tag = tag_name_tmp.lstrip()[:4]
        name = tag_name_tmp.lstrip()[4:].lstrip()

    #extract function/description
    function_tmp_1 = tag_name.next_sibling
    function_tmp_2 = ''.join(i for i in function_tmp_1 if not i.isdigit()).strip()

    if type == 'sd':
        function = (' '.join(function_tmp_2.split())).replace('Function: ','')
    if type == 'cd':
        function = (' '.join(function_tmp_2.split())).replace('Desc: ','')

    #extract data-element position and data-element code to build dictionary
    data_elements = []
    used_in = []
    a_tags = soup.find_all("a")
    for a_tag in a_tags:
        # find and extract data elements from <a> tags
        if len(a_tag.text) == 4:
            prev_sibling = a_tag.previous_sibling
            pattern = re.compile(r'\s[0-9]{3}\s')
            if pattern.search(prev_sibling):
                data_elem_pos_tmp = pattern.findall(prev_sibling)
                data_elem_pos = data_elem_pos_tmp[0].strip()
                # find status of data element in composite directory
                if type == 'cd' or type == 'sd':
                    if isinstance(a_tag.next_sibling, str):
                        pattern = re.compile(r' [A-Z]  ')
                        resultTmp = pattern.search(a_tag.next_sibling)
                        if resultTmp is not None:
                            status = resultTmp.group().strip()
                        else:
                            status = None
                    data_element = (data_elem_pos, a_tag.text, status)
                else:
                    data_element = (data_elem_pos, a_tag.text)
                data_elements.append(data_element)
        # find and extract message names from <a> tags
        elif type == 'sd' and len(a_tag.text) == 6:
            pattern = re.compile(r'[A-Z]{6}')
            if pattern.search(a_tag.text):
                message_name = a_tag.text
                used_in.append(message_name)
        # find and extract segment names from <a> tags
        elif type == 'cd' and len(a_tag.text) == 3 and not a_tag.text.isdigit():
            pattern = re.compile(r'[A-Z]{3}')
            if pattern.search(a_tag.text):
                segment_name = a_tag.text
                used_in.append(segment_name)

    if type == 'sd':
        item = Segment(tag, name, function, data_elements, used_in, url)
    elif type == 'cd':
        item = Composite_data_element(tag, name, function, data_elements, used_in, url)
    return item

def get_data_element_from_soup(soup, type, url):
    """to scrap edifact directory pages (sd, cd, ed) (ex. https://service.unece.org/trade/untdid/d19a/trsd/trsdbgm.htm)
       build and return a segment, composite or data element object."""
    #extract tag and name
    tag_name = soup.find("h3")
    if tag_name.text.lstrip().startswith('X') or \
       tag_name.text.lstrip().startswith('|') or \
       tag_name.text.lstrip().startswith('-'):
        tag_name_tmp = tag_name.text.lstrip()[3:]
    else:
        tag_name_tmp = tag_name.text

    tag = tag_name_tmp.lstrip()[:4]
    name_tmp = tag_name_tmp.lstrip()[4:].strip()
    name = name_tmp[:-3].strip()

    function_format_tmp = tag_name.next_sibling
    function_format_tmp = function_format_tmp.strip().split('Repr:')
    function = function_format_tmp[0].strip()[6:]
    format_tmp = function_format_tmp[1].strip()
    format = format_tmp.split('\r\n\r\n')[0]

    #extract codes values, name and description
    textNodes = soup.findAll(text=True)
    has_code_values = False
    code_list = []
    for i, textNode in enumerate(textNodes):
        if 'Code Values: ' in textNode:
            has_code_values = True
            pos = i

    if has_code_values:
        codes_tmp = textNodes[pos+1]
        for i, code_block in enumerate(codes_tmp.split('.\r\n\r\n')):
            if len(code_block.strip()) > 0:
                code_block_str = code_block.replace('|', '').strip()
                code_value_name_tmp = ''
                code_desc_tmp = ''

                for line in code_block_str.split('\r\n'):
                    if re.match(r'^[0-9]{1,2}  ', line):
                        code_value_name_tmp += line
                    elif line.startswith('              '):
                        code_desc_tmp += line
                    else:
                        code_value_name_tmp += line
                # some codes contain notes which will be in own code code_block
                # here we need to filter them.
                if not code_value_name_tmp.startswith('Note:'):
                    # codes which will be removed are flagged with "X".
                    # I need a logic to handle them, but some codes also start with "X".
                    # That's why I check also the length of the splitted list.
                    # Some data elements contain a "#". Not sure why. But I need to handle them.
                    # example: 5463
                    if (code_value_name_tmp.split('   ')[0].strip() == 'X' and \
                        len(code_value_name_tmp.split('   ')) == 3) or \
                        code_value_name_tmp.split('   ')[0].strip() == '#':
                        value = code_value_name_tmp.split('   ')[1].strip()
                        code_name = code_value_name_tmp.split('   ')[2].lstrip()
                    else:
                        value = code_value_name_tmp.split('   ')[0].strip()
                        code_name = code_value_name_tmp.split('   ')[1].lstrip()

                    desc = ' '.join(code_desc_tmp.split())
                    code_list.append(CodeItem(value, code_name, desc))
                else:
                    code_list[-1].description += '. ' + ' '.join(code_block_str.split())
    item = Data_element(tag, name, function, format, code_list, url)
    return item

def main():
    global verbose
    """used when executed from command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("version", type=check_version_type, help="EDIFACT release version (ex. d01a)")
    parser.add_argument("mode", nargs='?', type=str, choices={"tr", "ti"}, default='tr', \
                            help="Which EDIFACT mode: tr (batch) or ti (interactive)?")
    args = parser.parse_args()
    if args.verbose:
        print("verbosity turned on")
        verbose=True

    mode = args.mode
    version = args.version

    if verbose:
        print(verbose_text)

    # Get all segments from segment directory and write them in list
    # tags = get_tags_from_website('tr', 'd01b', 'sd')
    # segments = create_item_list('tr', 'd01b', tags, 'sd')
    # for segment in segments:
    #     segment.info()
    #     print('------------------------------')

    # Get all composite data elements from composite data element directory and write them in list
    # tags = get_tags_from_website('tr', 'd01b', 'cd')
    # composite_data_elements = create_item_list('tr', 'd01b', tags, 'cd')
    # for composite_data_element in composite_data_elements:
    #     composite_data_element.info()trsdbgm.htm.1
    #     print('------------------------------')

    # Get all data elements from element directory and write them in list
    # tags = get_tags_from_website('tr', 'd01b', 'ed')
    # data_elements = create_item_list('tr', 'd01b', tags, 'ed')
    # for data_element in data_elements:
    #     data_element.info()
    #     print('------------------------------')

    print('--------------------------')
    # TEST creationurl of specific segment
    #item = create_item('tr', 'd01a', 'BGM', 'sd')
    #item = create_item('tr', 'd01a', '3229', 'ed')
    #item.info()

    print('--------------------------')
    # TEST creation of composite data element
    item = create_item('tr', 'd01a', 'C002', 'cd')
    item.info()

    # TEST creation of specific data element
    #item = create_item('tr', 'd01a', '5463', 'ed')
    #item = create_item('tr', 'd01a', '1001', 'ed')
    #item.info()



if __name__ == "__main__":
    main()

# example links
#https://service.unece.org/trade/untdid/d19a/trsd/trsdapr.htm
#https://service.unece.org/trade/untdid/d19a/trsd/trsdi1.htm
#http://www.unece.org/trade/untdid/d95b/Welcome.html
#https://service.unece.org/trade/untdid/d01b/tred/tredi1.htm
