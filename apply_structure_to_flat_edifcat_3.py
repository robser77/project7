import logging
import argparse
import lxml.etree as etree
import sys

def check_xml_validity(xml):
    try:
        dom = etree.parse(xml)
    except NameError as error:
        print('No input xml specified: {}'.format(error))
        quit()
    except OSError as error:
        print('Failed to load input xml: {}'.format(xml))
        quit()
    except lxml.etree.XMLSyntaxError as error:
        print('Failed to parse input xml: {}'.format(error))
        quit()
    return dom

def traverse_struc(node, edi_segment_nodes, curr_output_node, indent):
    print('====================================')
    print('curr_group_node: {}'.format(indent + node.tag))

    start_segment_node = node.xpath('startsegment')
    start_segment_node_text = start_segment_node[0].text
    print('group start_segment: {}'.format(start_segment_node_text))
    end_segments = [segment.text for segment in node.xpath('endsegment')]
    print('group end_segments: {}'.format(end_segments))

    #next_groups = node.xpath('*[name() != "startsegment" and name() != "endsegment"]')
    #print(next_groups)
    #next_group = next_groups[0]
    #print('next group: {}'.format(next_group.tag))
    next_start_segments = [segment.text for segment in node.xpath('*/startsegment')]
    if len(next_start_segments) > 0:
        next_start_segment = next_start_segments[0]
        next_group = node.xpath('*[name() != "startsegment" and name() != "endsegment"]')[0]
        obligatory = next_group.get('obligatory')
        movetochild = next_group.get('movetochild')
    else:
        next_start_segment = ''
        next_group = ''
        obligatory = ''
        movetochild = ''
    print('next group start_segments: {}'.format(next_start_segments))
    if len(edi_segment_nodes) > 0:
        curr_input_edi_node = edi_segment_nodes[-1]
        curr_input_edi_node_tag = curr_input_edi_node.tag
    else:
        curr_input_edi_node_tag = 'XXX'
    print('curr_input_edi_node_tag: {}'.format(curr_input_edi_node_tag))
    print('---------------------------------')
    edi_segment_nodes_tags = [segment.tag for segment in edi_segment_nodes]
    iterate_edi_segments = True
    print('--- iterating over edi segments ... ')
    print('---   next startsegment {}'.format(next_start_segment))
    last_edi_segment = ''
    while iterate_edi_segments == True and \
          len(edi_segment_nodes) > 0:
        if obligatory == 'n':
            iterate_edi_segments = False
            print('HERE')
        elif curr_input_edi_node_tag == start_segment_node_text:
            print('   added {} to {}'.format(curr_input_edi_node_tag, node.tag))
            # in case same element as before move current node back to parent.
            if curr_input_edi_node_tag == last_edi_segment:
                print(curr_output_node)
                curr_output_node = curr_output_node.xpath('../.')[0]
                print(curr_output_node)
            # create group tag
            group = etree.SubElement(curr_output_node, node.tag)
            curr_output_node = group
            # add edifact segment to group
            curr_output_node.append(curr_input_edi_node)
            # discard used edifact element from list
            edi_segment_nodes.pop()
            curr_input_edi_node = edi_segment_nodes[-1]
            curr_input_edi_node_tag = curr_input_edi_node.tag
        # check if current edi segment is a group start list.
        elif curr_input_edi_node_tag in next_start_segments:
            iterate_edi_segments = False
            print('   STOP! reason: edi_segment in next start segment list:{}'.format(curr_input_edi_node_tag))
        # check if current edi segment is in group end list.
        elif curr_input_edi_node_tag in end_segments:
            iterate_edi_segments = False
            print('   STOP! reason: edi_segment in end segment list:{}'.format(curr_input_edi_node_tag))
            print('     curr_output_node: {}'.format(curr_output_node[0].tag))
            curr_output_node = curr_output_node.xpath('../.')[0]
            print('     back to parent: new curr_output_node: {}'.format(curr_output_node[0].tag))
            print('- - - - - - - - - - - - -')
        # otherwise, just append it to current output node.
        else:
            curr_output_node.append(curr_input_edi_node)
            edi_segment_nodes.pop()
            print('----should be added: input_edi_node_tag: {}'.format(curr_input_edi_node_tag))
            if len(edi_segment_nodes) > 0:
                curr_input_edi_node = edi_segment_nodes[-1]
                curr_input_edi_node_tag = curr_input_edi_node.tag
                print('   ----new: curr_input_edi_node_tag: {}'.format(curr_input_edi_node_tag))
        last_edi_segment = curr_input_edi_node_tag

    indent += '---'
    for child in node.xpath('*[name() != "startsegment" and \
                               name() != "endsegment"]'):

        curr_input_edi_node = edi_segment_nodes[-1]
        curr_input_edi_node_tag = curr_input_edi_node.tag
        child_start_segment = child.xpath('*[name() = "startsegment"]')[0].text
        print('     child group: {}'.format(indent + child.tag))
        print('     child group startsegment: {}'.format(child_start_segment))
        #print('start_segment_node_text: {}'.format(start_segment_node_text))
        print('     curr_input_edi_node_tag: {}'.format(curr_input_edi_node_tag))
        if (child.xpath('*') and \
            child_start_segment == curr_input_edi_node_tag) or \
            (child.get('obligatory') == 'n' and \
             child.get('movetochild') == 'y'):
            print('         - new_recursion -')
            traverse_struc(child, edi_segment_nodes, curr_output_node, indent)

def main():
    """used when executed from command line"""
    h_verbose = 'Increase output verbosity'
    h_input = 'Path and name to the flat edifact xml input file that you want to give structure to.'
    h_struc = 'Path and name to the xml edifact structure file that will be applied to the flat edifact xml.'
    h_output = 'Path and name to the structured xml ouput file that you want to create or "-" for stdout.'
    h_pretty = 'Pretty print output.'

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help=h_verbose, action="store_true")
    parser.add_argument("-i", "--input", help=h_input, nargs=1, required=True)
    parser.add_argument("-s", "--struc", help=h_struc, nargs=1, required=True)
    parser.add_argument("-o", "--output", help=h_output, nargs=1)
    parser.add_argument("-fo", "--pretty", help=h_pretty, action="store_true")

    args = parser.parse_args()
    if args.verbose:
        loglevel = 'INFO'
    else:
        loglevel = 'WARNING'
    if args.input:
        flat_edi_xml = args.input[0]
    if args.struc:
        edi_struc_xml = args.struc[0]
    if args.output:
        output_file = args.output[0]

    pretty_print = True if args.pretty else False

    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('verbosity turned on')

    flat = check_xml_validity(flat_edi_xml)
    flat_root = flat.getroot()

    struc = check_xml_validity(edi_struc_xml)
    struc_root = struc.getroot()

    edi_segment_nodes = []
    edi_segment_tags = []
    for edi_segment in flat_root.iterchildren(tag=etree.Element):
        edi_segment_nodes.append(edi_segment)
        edi_segment_tags.append(edi_segment.tag)
    edi_segment_nodes.reverse()
    edi_segment_tags.reverse()
    print(edi_segment_tags)

    #build output xml
    output_root = etree.Element('root')
    curr_output_node = output_root

    struc_root = struc.getroot()
    print('struc-root: {}'.format(struc_root.tag))
    indent = '---'
    traverse_struc(struc_root, edi_segment_nodes, curr_output_node, indent)

    logging.info('all done ...')

    if not args.output or output_file == '-' :
        try:
            sys.stdout.write(etree.tostring(output_root,
                                            pretty_print=pretty_print,
                                            encoding='unicode'))
        except TypeError as error:
            print('Failed to serialize flat edifact dom: {}'.format(error))
            quit()
    elif len(output_file) > 0:
        try:
            edifact_dom = etree.ElementTree(output_root)
            edifact_dom.write(output_file,
                              pretty_print=pretty_print,
                              encoding='UTF-8')
        except PermissionError as error:
            print('Failed to write to file: {}'.format(error))
        except AttributeError as error:
            print('Failed to write to file: {}'.format(error))
        quit()

if __name__ == "__main__":
    main()
