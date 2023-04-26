import sys
import re

# https://trac-hacks.org/ticket/11050#comment:13
_illegal_unichrs = ((0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
                    (0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
                    (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                    (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                    (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                    (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                    (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                    (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF))
_illegal_ranges = tuple("%s-%s" % (chr(low), chr(high))
                        for (low, high) in _illegal_unichrs
                        if low < sys.maxunicode)
_illegal_xml_chars_re = re.compile('[%s]' % ''.join(_illegal_ranges))

def _escape_match(match):
    return '&#%i;' % ord(match.group(0))

def escape_xml_invalid_chars(xml_text):
    return _illegal_xml_chars_re.sub(_escape_match, xml_text)

import glob
import xml
from xml.dom.minidom import Document

# Funtion to add a node into a book node, with text
def addNode(doc, book_node, name, text):
    node = doc.createElement(name)
    book_node.appendChild(node)

    text_node = doc.createTextNode(text)
    node.appendChild(text_node)
    return node

# Create an xml document
doc = Document()

# XML cannot have multiple root nodes, so create corpora to store swedish and english
corpora_node = doc.createElement("corpora")
doc.appendChild(corpora_node)
swe_node = doc.createElement("swedishcorpus")
corpora_node.appendChild(swe_node)
eng_node = doc.createElement("englishcorpus")
corpora_node.appendChild(eng_node)

# Find all files ending with .txt, in this folder
text_file_paths = sorted(glob.glob("*.txt"))

print("Found {} text files in this folder.\n".format(len(text_file_paths)))

# Loop through the files
for text_file_path in text_file_paths:
    # Create book node
    book_node = doc.createElement("book")

    # Remove the ending and split the string on whitespace
    elements = text_file_path.rstrip(".txt").split(" ")

    # Check that the number of elements are correct
    if len(elements) != 6 and len(elements) != 7:
        print("Wrong number of elements in file name, so the file was skipped. Expected 6, but got {} elements. The file was: \"{}\"".format(len(elements), text_file_path))
        continue

    # Split the elements into separate variables
    if len(elements) == 6:
        year, uni, author, language, disstype, gender = elements
    else:
        year, uni, author, language, disstype, gender, addinfo = elements

    addNode(doc, book_node, "id", text_file_path)
    addNode(doc, book_node, "year", year)
    addNode(doc, book_node, "uni",  uni)
    addNode(doc, book_node, "author",   author)
    addNode(doc, book_node, "language", language)
    addNode(doc, book_node, "disstype", disstype)
    addNode(doc, book_node, "gender",   gender)

    if len(elements) == 7:
        addNode(doc, book_node, "addinfo",  addinfo)

    text_content = ""

    # Read the content of the file
    try:
        with open(text_file_path, "r") as text_file:
            text_content = text_file.read()
            text_content = text_content.encode(encoding="latin1", errors="ignore").decode(encoding="latin1")
            text_content = escape_xml_invalid_chars(text_content)

    except Exception as e:
        print("Could not open file \"{}\", so the file was skipped. Exception:".format(text_file_path))
        print(e.strerror + "\n")
        pass

    text_split = re.split("\*main\*|\*sum\*|\*post\*", text_content)

    if len(text_split) != 4:
        print("Incorrect number (not n=4) of splitters on: " + text_file_path)
        continue

    pre_text, main_text, sum_text, post_text = text_split

    pre_node = addNode(doc, book_node, "pre_text", pre_text)
    main_node = addNode(doc, book_node, "main_text", main_text)
    sum_node = addNode(doc, book_node, "sum_text", sum_text)
    post_node = addNode(doc, book_node, "post_text", post_text)

    # Add the book node to the corpus
    if language == "swe":
        pre_node.setAttribute("lang", "sv")
        main_node.setAttribute("lang", "sv")
        sum_node.setAttribute("lang", "en")
        post_node.setAttribute("lang", "en")
        swe_node.appendChild(book_node)
    else:
        pre_node.setAttribute("lang", "en")
        main_node.setAttribute("lang", "en")
        sum_node.setAttribute("lang", "sv")
        post_node.setAttribute("lang", "en")
        eng_node.appendChild(book_node)
        pass

xml_file_path = "converted.xml"

# Write the XML file to disk
try:
    with open(xml_file_path, "w") as xml_file:
        doc.writexml(xml_file, indent="", addindent=" ", newl="\n", encoding="UTF-8")
except Exception as e:
    print("Could save the xml file \"{}\". Exception:".format(xml_file_path))
    print(e.strerror + "\n")
