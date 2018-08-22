

from lxml import etree

def conver_element(element):
        foo = recursive_dict(element)
        return foo

def recursive_dict( element):
    return element.tag, \
           dict(map(recursive_dict, element)) or element.text

root2 = etree.parse("CountryList.xml")


j =[]

import sys

for i in root2.getiterator():

    a,b = recursive_dict(i)
    try:
        if "Country" in b:
            j.append(b["Country"])
        else:
            j.append(b)
    except Exception as e:
        print("error")
        sys.exit()

import json

jstr = json.dumps(j,indent=2)
print(jstr)