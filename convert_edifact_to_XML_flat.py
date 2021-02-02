import logging
import argparse
import lxml.etree as etree
import sys

def convert_to_xml_flat(data):
    component_data_element_separator = ':'
    data_element_separator = '+'
    decimal_mark = '.'
    release_charcater = '?'
    segment_terminator = "'"
    data = data.replace('\n', '')
    logging.info('starting conversion...')

    if data.startswith('UNA'):
        UNA_segment = data[0:9]
        logging.info('Special characters used to '
                      + 'interpret the the message: {}'.format(UNA_segment))
        component_data_element_separator = UNA_segment[3]
        data_element_separator = UNA_segment[4]
        decimal_mark = UNA_segment[5]
        release_charcater = UNA_segment[6]
        segment_terminator = UNA_segment[8]

    special_characters = component_data_element_separator \
                         + data_element_separator \
                         + decimal_mark \
                         + release_charcater \
                         + segment_terminator

    root = etree.Element('root')
    for count, line in enumerate(data.split(segment_terminator)):
        if count == 1 and not (line.startswith('UNB') or line.startswith('UNA')):
            logging.warning('Edifact not starting with UNA or UNB segment!')

        elements = line.split('+')
        tag_name = elements[0][0:3]
        if len(tag_name) > 0: tag = etree.SubElement(root, tag_name)
        if tag_name == 'UNA':
            tag.set('special_characters', special_characters)

        if tag_name != 'UNA':
            for counter, element in enumerate(elements):
                if ':' in element:
                    composites = element.split(':')
                    pos = counter * 10
                    composite_tag_name = 'COMPOSITE_' + str(pos)
                    composite_tag = etree.SubElement(tag, composite_tag_name)
                    for counter2, component in enumerate(composites, start = 1):
                        sub_pos = counter2 * 10
                        component_tag_name = 'COMPONENT_' + str(pos) + '_' + str(sub_pos)
                        component_tag = etree.SubElement(composite_tag, component_tag_name)
                        component_tag.text = component
                elif counter > 0:
                    simple = element
                    pos = counter * 10
                    simple_tag_name = 'SIMPLE_' + str(pos)
                    simple_tag = etree.SubElement(tag, simple_tag_name)
                    simple_tag.text = simple
    return root

def main():
    """used when executed from command line"""
    h_verbose = 'Increase output verbosity'
    h_input = 'Path and name to the edifact input file that you want to transform.'
    h_output = 'Path and name to the output xml file that you want to create or "-" for stdout.'
    h_pretty = 'Pretty print output.'

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help=h_verbose, action="store_true")
    parser.add_argument("-i", "--input", help=h_input, nargs=1)
    parser.add_argument("-o", "--output", help=h_output, nargs=1)
    parser.add_argument("-fo", "--pretty", help=h_pretty, action="store_true")

    args = parser.parse_args()
    if args.verbose:
        loglevel = 'INFO'
    else:
        loglevel = 'WARNING'
    if args.input:
        std_in = False
        input_file = args.input[0]
        try:
            with open(input_file, 'r') as file:
                data = file.read()
        except OSError as error:
            print('Failed to load input xml: {}'.format(xml_input))
            quit()
    else:
        std_in = True
        data = sys.stdin.read()
        if len(data) == 0:
            quit()
    if args.output:
        output_file = args.output[0]

    pretty_print = True if args.pretty else False

    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('verbosity turned on')

    edifact_dom_flat = convert_to_xml_flat(data)

    if not args.output or output_file == '-' :
        try:
            sys.stdout.write(etree.tostring(edifact_dom_flat,
                                            pretty_print=pretty_print,
                                            encoding='unicode'))
        except TypeError as error:
            print('Failed to serialize flat edifact dom: {}'.format(error))
            quit()
    elif len(output_file) > 0:
        try:
            edifact_dom_flat.write(output_file,
                                   pretty_print=pretty_print,
                                   encoding='UTF-8')
        except PermissionError as error:
            print('Failed to write to file: {}'.format(error))
        except AttributeError as error:
            print('Failed to write to file: {}'.format(error))
        quit()

if __name__ == "__main__":
    main()
