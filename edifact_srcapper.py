import argparse
import re
import requests
import time
from bs4 import BeautifulSoup
from xml.etree import ElementTree as et
from datetime import datetime

#TODO start
# Quality Checks
# Create light-weight XML by reducing tag names to minimum
# Check if toXml methods can be unified
#
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
        my_info = 'tag: {}\n'.format(self.tag)
        my_info += 'name: {}\n'.format(self.name)
        my_info += 'function: {}\n'.format(self.function)
        my_info += 'url: {}\n'.format(self.url)
        my_info += 'data elements: \n'
        for data_element in self.data_elements:
            my_info += '{}|{}|{}\n'.format(data_element[0], data_element[1], data_element[2])
        my_info += 'used in messages:'
        for message in self.used_in_messages:
            my_info += '{}|'.format(message)
        my_info += '\n'
        return my_info

class Composite_data_element(Item):
    def __init__(self, tag, name, function, data_elements, used_in_segments, url):
        super().__init__(tag, name, function)
        self.data_elements = data_elements
        self.used_in_segments = used_in_segments
        self.url = url

    def info(self):
        my_info = 'tag: {}\n'.format(self.tag)
        my_info += 'name: {}\n'.format(self.name)
        my_info += 'function: {}\n'.format(self.function)
        my_info += 'url: {}\n'.format(self.url)
        my_info += 'data elements: \n'
        for data_element in self.data_elements:
            my_info += '{}|{}|{}\n'.format(data_element[0], data_element[1], data_element[2])
        my_info += 'used in segments:'
        for message in self.used_in_segments:
            my_info += '{}|'.format(message)
        my_info += '\n'
        return my_info

class Data_element(Item):
    def __init__(self, tag, name, function, format, code_list, url):
        super().__init__(tag, name, function)
        self.format = format
        self.code_list = code_list
        self.url = url

    def info(self):
        my_info = 'tag: {}\n'.format(self.tag)
        my_info += 'name: {}\n'.format(self.name)
        my_info += 'function: {}\n'.format(self.function)
        my_info += 'fornat: {}\n'.format(self.format)
        my_info += 'url: {}\n'.format(self.url)
        my_info += 'codes: \n'
        for code in self.code_list:
            my_info += '{}|{}|{}\n'.format(code.value, code.name, code.description)
        return my_info

class CodeItem():
    def __init__(self, value, name, description):

        self.value = value
        self.name = name
        self.description = description

class Dir():
    def __init__(self, version, mode):
        self.version = version
        self.mode = mode

    def toXML(self, filename):
        tree = self.toElementTree(False)
        with open(filename, 'wb') as f:
            tree.write(f, encoding='utf-8')

    def toXML_string(self):
        tree = self.toElementTree(False)
        root = tree.getroot()
        xml_str = et.tostring(root, encoding='unicode')
        print(BeautifulSoup(xml_str, 'xml').prettify())

class Segment_Dir(Dir):
    def __init__(self, version, mode, segments):
        super().__init__(version, mode)
        self.segments = segments

    def toElementTree(self, add_used_in):
        """returns an ElementTree Object of the segment directory."""
        root = et.Element('segment_dir')
        tree = et.ElementTree(root)

        for i, segment in enumerate(self.segments):

            if verbose:
                print('{} segment to XML Node...'.format(segment.tag))

            segment_tag = et.Element('segment')
            segment_tag.set('tag', segment.tag)
            segment_tag.set('url', segment.url)
            name = et.Element('name')
            name.text = segment.name
            segment_tag.append(name)
            function = et.Element('function')
            function.text = segment.function
            segment_tag.append(function)
            data_elements = et.Element('data_elements')
            for data_element in segment.data_elements:
                data_element_tag = et.Element('data_element')
                data_element_tag.set('pos', str(data_element[0]))
                #pos = et.Element('pos_' + str(data_element[0]))
                data_element_tag.set('status', data_element[2])
                if data_element[1].startswith('C'):
                    type = 'composite'
                else:
                    type = 'simple'
                data_element_tag.set('type', type)
                data_element_tag.text = data_element[1]
                data_elements.append(data_element_tag)
            segment_tag.append(data_elements)
            if add_used_in is True:
                used_in = et.Element('used_in')
                for message in segment.used_in_messages:
                    message_tag = et.Element('message')
                    message_tag.text = message
                    used_in.append(message_tag)
                segment_tag.append(used_in)
            root.append(segment_tag)
        return tree

class Composite_Dir(Dir):
    def __init__(self, version, mode, composite_elements):
        super().__init__(version, mode)
        self.composite_elements = composite_elements

    def toElementTree(self, add_used_in):
        """returns an ElementTree Object of the composite directory."""
        root = et.Element('composite_dir')
        tree = et.ElementTree(root)

        for i, composite_element in enumerate(self.composite_elements):
            if verbose:
                print('{} composite_data_element to XML Node...'.format(composite_element.tag))

            composite_element_tag = et.Element('composite_data_element')
            composite_element_tag.set('tag', composite_element.tag)
            composite_element_tag.set('url', composite_element.url)
            name = et.Element('name')
            name.text = composite_element.name
            composite_element_tag.append(name)
            function = et.Element('function')
            function.text = composite_element.function
            composite_element_tag.append(function)
            data_elements = et.Element('data_elements')
            for data_element in composite_element.data_elements:
                data_element_tag = et.Element('data_element')
                data_element_tag.set('pos', str(data_element[0]))
                data_element_tag.set('status', data_element[2])
                data_element_tag.text = data_element[1]
                data_elements.append(data_element_tag)
            composite_element_tag.append(data_elements)
            used_in = et.Element('used_in')
            for segment in composite_element.used_in_segments:
                segment_tag = et.Element('segment')
                segment_tag.text = segment
                used_in.append(segment_tag)
            composite_element_tag.append(used_in)
            root.append(composite_element_tag)
        return tree

class Element_Dir(Dir):
    def __init__(self, version, mode, data_elements):
        super().__init__(version, mode)
        self.data_elements = data_elements

    def toElementTree(self, add_used_in):
        """returns an ElementTree Object of the data element directory."""
        root = et.Element('element_dir')
        tree = et.ElementTree(root)

        for i, data_element in enumerate(self.data_elements):
            if verbose:
                print('{} data_element to XML Node...'.format(data_element.tag))
            data_element_tag = et.Element('data_element')
            data_element_tag.set('tag', data_element.tag)
            data_element_tag.set('url', data_element.url)
            name = et.Element('name')
            name.text = data_element.name
            data_element_tag.append(name)
            function = et.Element('function')
            function.text = data_element.function
            data_element_tag.append(function)
            format = et.Element('format')
            format.text = data_element.format
            data_element_tag.append(format)
            codes = et.Element('codes')
            for code in data_element.code_list:
                code_tag = et.Element('code')
                value = et.Element('value')
                value.text = code.value
                code_tag.append(value)
                name = et.Element('name')
                name.text = code.name
                code_tag.append(name)
                description = et.Element('description')
                description.text = code.description
                code_tag.append(description)
                codes.append(code_tag)
            data_element_tag.append(codes)
            root.append(data_element_tag)
        return tree

class Edifact_Dir(Dir):
    def __init__(self, version, mode):
        super().__init__(version, mode)

    def create_segment_directory_tree(self):
        """Returns an ElementTree Object of the segment directory."""
        tags = get_tags_from_website(self.version, self.mode, 'sd')
        segments = create_item_list(self.version, self.mode, tags, 'sd')
        return Segment_Dir(self.version, self.mode, segments).toElementTree(False)

    def create_composite_directory_tree(self):
        """Returns an ElementTree Object of the composite directory."""
        tags = get_tags_from_website(self.version, self.mode, 'cd')
        composite_elements = create_item_list(self.version, self.mode, tags, 'cd')
        return Composite_Dir(self.version, self.mode, composite_elements).toElementTree(False)

    def create_data_element_directory_tree(self):
        """Returns an ElementTree Object of the data element directory."""
        tags = get_tags_from_website(self.version, self.mode, 'ed')
        data_elements = create_item_list(self.version, self.mode, tags, 'ed')
        return Element_Dir(self.version, self.mode, data_elements).toElementTree(False)

    def create(self):
        """returns an ElementTree Object of the edifact directory."""
        segment_dir_tree = self.create_segment_directory_tree()
        composite_dir_tree = self.create_composite_directory_tree()
        data_element_dir_tree = self.create_data_element_directory_tree()

        root = et.Element('edifact_directory')
        tree = et.ElementTree(root)
        root.set('version', self.version)
        root.set('mode', self.mode)
        root.append(segment_dir_tree.getroot())
        root.append(composite_dir_tree.getroot())
        root.append(data_element_dir_tree.getroot())
        return tree

    def toXML(self, filename, tree):
        """writes a tree to an XML file."""
        with open(filename, 'wb') as f:
            tree.write(f, encoding='utf-8')

class Message_Structure():
    def __init__(self, version, mode, message_type):
        self.version = version
        self.mode = mode
        self.message_type = message_type

    def toElementTree(self):
        URL = base_URL + self.version.lower() + '/' + self.mode + 'md' + '/' + self.message_type.lower() + '_c.htm'
        tree = None

        page = get_page_from_URL(URL)
        if page is not None:
            soup = BeautifulSoup(page.content, 'html.parser')
            tree = create_message_element_tree_from_soup(soup, 'orders', URL)
        return tree

    def toXML(self, filename):
        tree = self.toElementTree()
        with open(filename, 'wb') as f:
            tree.write(f, encoding='utf-8')

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
        title = soup.find("title").text
        if title == '404 Not Found':
            raise requests.HTTPError(title)
        else:
            if verbose: print('OK')
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
        try:
            item = create_item(mode, version, tag, type)
        except requests.HTTPError as error:
            print(error)
            continue
        else:
            items.append(item)
    if verbose: print('Build {} items out of {} tags from {}.'.format(len(items), len(tags), type),  end = '')
    if verbose and len(items) == len(tags): print(' - Looks good!')
    elif verbose: print(' - Oops, something is missing!')
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
    # TODO: check in cd if this creates valid output.
    #function_tmp_2 = ''.join(i for i in function_tmp_1 if not i.isdigit()).strip()
    function_tmp_2 = ''.join(i for i in function_tmp_1).strip()
    if function_tmp_2[-3:] == '010':
        function_tmp_3 = function_tmp_2[:-3]
    elif function_tmp_2[-5:] == '010 X':
        function_tmp_3 = function_tmp_2[:-5]
    else:
        function_tmp_3 = function_tmp_2
    #print('function1: |{}|'.format(function_tmp_1))
    #print('function2: |{}|'.format(function_tmp_2))

    if type == 'sd':
        function = (' '.join(function_tmp_3.split())).replace('Function: ','')
    if type == 'cd':
        function = (' '.join(function_tmp_3.split())).replace('Desc: ','')

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
                        pattern = re.compile(r' [A-Z] ')
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
                        code_value_name_tmp.split('   ')[0].strip() == '#' or \
                        code_value_name_tmp.split('   ')[0].strip() == '+':
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

def get_message_types_from_website(mode, version, type):
    """ get all message names from website and return a list including message names. """
    pass

def create_message_element_tree_from_soup(soup, message_type, url):
    """ create message structure from soup and return element tree. """
    a_tags = soup.find_all("a")
    root = et.Element(message_type)
    root.set('url', url)
    now = datetime.now()
    now_formatted = now.strftime("%Y-%m-%dT%H:%M:%S")
    root.set('creation_date', now_formatted)
    tree = et.ElementTree(root)
    curr_node_stack = []
    curr_node_stack.append(root)
    curr_parent_node = root
    if verbose:
        print('Message Type: {}'.format(message_type.upper()))
    for a_tag in a_tags:
        status = 'unknown'
        recurrence = 'unknown'
        if (re.match(r'[A-Z]{3}', a_tag.text) and \
            (' M ' in a_tag.next_sibling or \
             ' C ' in a_tag.next_sibling)) or \
            (re.match(r'[0-9]{4}', a_tag.text) and
             '-- Segment group ' in a_tag.next_sibling):
            # Segments which do not pertain to a group
            # just add them to root
            if '|' not in a_tag.next_sibling and \
               '+' not in a_tag.next_sibling and \
                not(re.match(r'[0-9]{4}', a_tag.text)):
                if verbose:
                    print('---|{}|'.format(a_tag.text))
                node = et.Element(a_tag.text)
                # add status attribute
                if ' M ' in a_tag.next_sibling:
                    status = 'M'
                elif ' C ' in a_tag.next_sibling:
                    status = 'C'
                node.set('status', status)
                # add recurrence attribute
                pattern = re.compile(' [0-9]{1,6} ')
                recurrence_tmp = pattern.search(a_tag.next_sibling)
                recurrence = recurrence_tmp.group().strip()
                node.set('recurrence', recurrence)
                # set actual parent node
                curr_parent_node = root
                curr_parent_node.append(node)
            elif 'Segment group' in a_tag.next_sibling:
                pattern = re.compile('Segment group [0-9]{1,3}')
                seg_group_tmp = pattern.search(a_tag.next_sibling)
                seg_group = seg_group_tmp.group().replace(' ', '_').lower()
                filler = '---' * (a_tag.next_sibling.count('|') + 1)
                if verbose:
                    print('-{}|{}|'.format(filler, seg_group))
                node = et.Element(seg_group)
                #add status attribute
                if ' M ' in a_tag.next_sibling:
                    status = 'M'
                elif ' C ' in a_tag.next_sibling:
                    status = 'C'
                node.set('status', status)
                # add recurrence attribute
                pattern = re.compile(' [0-9]{1,6}--')
                recurrence_tmp = pattern.search(a_tag.next_sibling)
                recurrence = recurrence_tmp.group().replace('--','').strip()
                node.set('recurrence', recurrence)

                depth = a_tag.next_sibling.count('|')

                if depth == 0:
                    curr_parent_node = root
                    curr_parent_node.append(node)
                    if len(curr_node_stack) > 1:
                        curr_node_stack = curr_node_stack[:1]
                    curr_node_stack.append(node)
                elif depth > 0:
                    if depth == len(curr_node_stack) - 1:
                        curr_parent_node = curr_node_stack[-1]
                        curr_parent_node.append(node)
                        curr_node_stack.append(node)
                    elif depth < len(curr_node_stack) - 1:
                        diff = (len(curr_node_stack) - 1) - depth
                        curr_node_stack = curr_node_stack[:-diff]
                        curr_parent_node = curr_node_stack[-1]
                        curr_parent_node.append(node)
                        curr_node_stack.append(node)

            elif (re.match(r'[A-Z]{3}', a_tag.text)):
                next_sibling = a_tag.next_sibling.split('\n')[0]
                counter = next_sibling.count('|') + next_sibling.count('+')
                filler = '---' * (counter)
                if verbose:
                    print('---{}|{}|'.format(filler, a_tag.text))
                node = et.Element(a_tag.text)
                #add status attribute
                if ' M ' in a_tag.next_sibling:
                    status = 'M'
                elif ' C ' in a_tag.next_sibling:
                    status = 'C'
                node.set('status', status)
                # add recurrence attribute
                if '--' in a_tag.next_sibling:
                    pattern = re.compile(' [0-9]{1,6}--')
                else:
                    pattern = re.compile(' [0-9]{1,6} ')
                recurrence_tmp = pattern.search(a_tag.next_sibling)
                if '--' in a_tag.next_sibling:
                    recurrence = recurrence_tmp.group().replace('--' ,'').strip()
                else:
                    recurrence = recurrence_tmp.group().strip()
                node.set('recurrence', recurrence)
                curr_parent_node = curr_node_stack[-1]
                curr_parent_node.append(node)
    return tree

def string_to_file(my_string, filename):
    with open(filename, 'wb') as f:
         f.write(my_string.encode('utf-8'))

def check_segment_tag(tag):
    return check_tag(tag, 's')

def check_composite_tag(tag):
    return check_tag(tag, 'c')

def check_element_tag(tag):
    return check_tag(tag, 'e')

def check_tag(tag, type):
    if type is 's':
        type_name = 'Segment'
        pat=re.compile(r"^[a-zA-Z]{3}$")
    if type == 'c':
        type_name = 'Composite Element'
        pat=re.compile(r"^[cC][0-9]{3}$")
    if type == 'e':
        type_name = 'Data Element'
        pat=re.compile(r"^[0-9]{4}$")
    error = 'Invalid formatting of {}: {}'.format(type_name, tag)
    if (not pat.match(tag) and tag != 'full') and __name__ == "__main__":
        raise argparse.ArgumentTypeError(error)
    elif not pat.match(tag) and tag != 'full':
        raise ValueError(error)
    return tag

def main():
    global verbose
    """used when executed from command line"""

    # help texts
    h_verbose = 'Increase output verbosity'
    h_version = 'EDIFACT release version (ex. d01a)'
    h_mode = 'Which EDIFACT mode: tr (batch) or ti (interactive)?'
    h_segment = 'Get specific text description of segment  from segment directory'
    h_composite = 'Get specific text description of composite element from composite directory'
    h_element = 'Get specific text description of data element from segment element directory'
    h_sd = 'Get specific segments from segment directory and ouput \
            as xml. Provide comma-separated list of segment tags or "full" for complete directory.'
    h_cd = 'Get specific composite elements from composite directory and ouput \
            as xml. Provide comma-separated list of composite element tags or "full" for complete directory.'
    h_ed = 'Get specific data elements from element directory and ouput \
            as xml. Provide comma-separated list of data element tags or "full" for complete directory.'
    h_full_edifact_dir = 'Get all and complete directories (sd, cd, ed) and ouput \
                          in one xml file.'
    h_output = 'Provide filename of ouput file'
    h_xml_version = 'Define if you want full word tags or abbreviated tag names (less heavy output).'

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help=h_verbose, action="store_true")
    parser.add_argument("version", type=check_version_type, help=h_version)
    parser.add_argument("mode", nargs='?', type=str, choices={"tr", "ti"}, default='tr', help=h_mode)
    parser.add_argument("-s", "--segment", type=check_segment_tag, help=h_segment, nargs=1)
    parser.add_argument("-c", "--composite", type=check_composite_tag, help=h_composite, nargs=1)
    parser.add_argument("-e", "--element", type=check_element_tag, help=h_element, nargs=1)
    parser.add_argument("-sd", "--segment_dir", help=h_sd, nargs=1)
    parser.add_argument("-cd", "--composite_dir", help=h_cd, nargs=1)
    parser.add_argument("-ed", "--element_dir", help=h_ed, nargs=1)
    parser.add_argument("-f", "--full_edifact_dir", help=h_full_edifact_dir, action="store_true")
    parser.add_argument("-o", "--output_file", help=h_output, nargs=1)
    parser.add_argument("-xml", "--xml_version", help=h_xml_version, nargs=1)

    args = parser.parse_args()
    if args.verbose:
        print("verbosity turned on")
        verbose=True
    mode = args.mode
    version = args.version
    # Create single tags as text output
    if args.segment or args.composite or args.element:
        if args.segment:
            type = 'sd'
            tag = args.segment[0]
        elif args.composite:
            type = 'cd'
            tag = args.composite[0]
        elif args.element:
            type = 'ed'
            tag = args.element[0]
        try:
            item = create_item(mode, version, tag, type)
        except requests.HTTPError as error:
            print(error)
        else:
            if item is not None:
                if args.output_file:
                    string_to_file(item.info(), args.output_file[0])
                else:
                    print(item.info())

    # Create full edifact directory
    if args.full_edifact_dir:
        my_edifact_dir = Edifact_Dir(mode, version)
        edifact_dir = my_edifact_dir.create()
        if args.output_file:
            filename = args.output_file[0]
        else:
            filename = 'output.xml'
        if verbose: print('Writing XMLfile: {}'.format(filename))
        my_edifact_dir.toXML(filename, edifact_dir)

    # Create full segment directory
    if args.segment_dir and args.segment_dir[0] == 'full':
        my_edifact_dir = Edifact_Dir(mode, version)
        my_seg_dir = my_edifact_dir.create_segment_directory_tree()
        if args.output_file:
            filename = args.output_file[0]
        else:
            filename = 'output.xml'
        if verbose: print('Writing XMLfile: {}'.format(filename))
        my_edifact_dir.toXML(filename, my_seg_dir)

    # Create full composite directory
    elif args.composite_dir and args.composite_dir[0] == 'full':
        my_edifact_dir = Edifact_Dir(mode, version)
        my_comp_dir = my_edifact_dir.create_composite_directory_tree()
        if args.output_file:
            filename = args.output_file[0]
        else:
            filename = 'output.xml'
        if verbose: print('Writing XMLfile: {}'.format(filename))
        my_edifact_dir.toXML(filename, my_comp_dir)

    # Create full element directory
    elif args.element_dir and args.element_dir[0] == 'full':
        my_edifact_dir = Edifact_Dir(mode, version)
        my_ele_dir = my_edifact_dir.create_data_element_directory_tree()
        if args.output_file:
            filename = args.output_file[0]
        else:
            filename = 'output.xml'
        if verbose: print('Writing XMLfile: {}'.format(filename))
        my_edifact_dir.toXML(filename, my_ele_dir)

    # Create xml directories based on given tags
    elif args.segment_dir or args.composite_dir or args.element_dir:
        if args.segment_dir:
            tags = args.segment_dir[0].split(',')
            function = check_segment_tag
            type = 'sd'
        elif args.composite_dir:
            tags = args.composite_dir[0].split(',')
            function = check_composite_tag
            type = 'cd'
        elif args.element_dir:
            tags = args.element_dir[0].split(',')
            function = check_element_tag
            type = 'ed'
        errors = list()
        for tag in tags:
            try:
                function(tag)
            except argparse.ArgumentTypeError as error:
                errors.append(error)
        if len(errors) > 0:
            for error in errors:
                print('Error: {}'.format(error))
            quit()

        items = create_item_list(mode, version, tags, type)
        if type == 'sd':
            my_dir = Segment_Dir(mode, version, items)
        elif type == 'cd':
            my_dir = Composite_Dir(mode, version, items)
        elif type == 'ed':
            my_dir = Element_Dir(mode, version, items)

        if args.output_file:
            my_dir.toXML(args.output_file[0])
        else:
            my_dir.toXML_string()

    if verbose:
        print(verbose_text)


    # edifact_dir = my_edifact_dir.create()
    # my_edifact_dir.toXML('edifact_dir.xml', edifact_dir)

    # Test creation of message structure
    # my_orders = Message_Structure(version, mode, 'ORDERS')
    # my_orders.toXML('test_order_structure.xml')

if __name__ == "__main__":
    main()

# example links
#https://service.unece.org/trade/untdid/d19a/trsd/trsdapr.htm
#https://service.unece.org/trade/untdid/d19a/trsd/trsdi1.htm
#http://www.unece.org/trade/untdid/d95b/Welcome.html
#https://service.unece.org/trade/untdid/d01b/tred/tredi1.htm
