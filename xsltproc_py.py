import logging
import argparse
import lxml.etree as etree
import sys

def main():
    """used when executed from command line"""

    h_verbose = 'Increase output verbosity'
    h_xslt = 'Path and name to the xslt script used to transform input file.'
    h_input = 'Path and name to the XML input file that you want to transform.'
    h_output = 'Path and name to the output file that you want to create or "-" for stdout.'
    h_pretty = 'Pretty print output.'

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help=h_verbose, action="store_true")
    parser.add_argument("-x", "--xslt", help=h_xslt, nargs=1, required=True)
    parser.add_argument("-i", "--input", help=h_input, nargs=1)
    parser.add_argument("-o", "--output", help=h_output, nargs=1)
    parser.add_argument("-fo", "--pretty", help=h_pretty, action="store_true")

    args = parser.parse_args()
    if args.verbose:
        loglevel = 'INFO'
    else:
        loglevel = 'WARNING'
    if args.xslt:
        xslt_name = args.xslt[0]
    if args.input:
        xml_input = args.input[0]
        std_in = False
    else:
        std_input = sys.stdin.read()
        if len(std_input) == 0:
            quit()
        std_in = True
    if args.output:
        output_file = args.output[0]

    pretty_print = True if args.pretty else False

    numeric_level = getattr(logging, loglevel.upper())
    logging.basicConfig(level=numeric_level)

    if std_in == False:
        try:
            dom = etree.parse(xml_input)
        except NameError as error:
            print('No input xml specified: {}'.format(error))
            quit()
        except OSError as error:
            print('Failed to load input xml: {}'.format(xml_input))
            quit()
        except lxml.etree.XMLSyntaxError as error:
            print('Failed to parse input xml: {}'.format(error))
    else:
        try:
            dom = etree.fromstring(std_input)
        except etree.XMLSyntaxError as error:
            print('Failed to parse input xml: {}'.format(error))
            quit()
    try:
        xslt = etree.parse(xslt_name)
    except NameError as error:
        print('No xslt script specified: {}'.format(error))
        quit()
    except OSError as error:
        print('Failed to load xslt script: {}'.format(xslt_name))
        quit()

    transform = etree.XSLT(xslt)
    newdom = transform(dom)

    if not args.output or output_file == '-' :
        sys.stdout.write(etree.tostring(newdom, pretty_print=pretty_print, encoding='unicode'))
    elif len(output_file) > 0:
        try:
            newdom.write(output_file, pretty_print=pretty_print, encoding='UTF-8')
        except PermissionError as error:
            print('Failed to write to file: {}'.format(error))
            quit()

if __name__ == "__main__":
    main()
