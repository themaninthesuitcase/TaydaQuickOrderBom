#
#  Python script to generate a Tayda Quick Order csv
#

"""
    @package
    Output: CSV (comma-separated)
    Grouped By: Tayda Part number
    Sorted By: Ref
    Fields: sku, qty

    Exports all parts with a Tayda part reference and the required qty.

    Command line:
    python "pathToFile/bom_group_tayda.py" "%I" "%O_Tayda.csv"
"""

# Import the KiCad python helper module and the csv formatter
import kicad_netlist_reader
import csv
import sys
import os

taydaField = "Tayda"

# from kicad_utils.py
def open_file_write(path, mode):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    dir_path = os.path.dirname(path)

    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    return open(path, mode)

# A helper function to convert a UTF8/Unicode/locale string read in netlist
# for python2 or python3 (Windows/unix)
def fromNetlistText( aText ):
    currpage = sys.stdout.encoding      #the current code page. can be none
    if currpage is None:
        return aText
    if currpage != 'utf-8':
        try:
            return aText.encode('utf-8').decode(currpage)
        except UnicodeDecodeError:
            return aText
    else:
        return aText

def myEqu(self, other):
    """myEqu is a more advanced equivalence function for components which is
    used by component grouping. Normal operation is to group components based
    on their value and footprint.

    This version overrides to only care about the custom field 'Tayda'.
    """
    result = True
    if self.getField(taydaField) != other.getField(taydaField):
        result = False

    return result

# Override the component equivalence operator - it is important to do this
# before loading the netlist, otherwise all components will have the original
# equivalency operator.
kicad_netlist_reader.comp.__eq__ = myEqu

if len(sys.argv) != 3:
    print("Usage ", __file__, "<generic_netlist.xml> <output.csv>", file=sys.stderr)
    sys.exit(1)

# Generate an instance of a generic netlist, and load the netlist tree from
# the command line option. If the file doesn't exist, execution will stop
net = kicad_netlist_reader.netlist(sys.argv[1])

# Open a file to write to, if the file cannot be opened output to stdout
# instead
try:
    f = open_file_write(sys.argv[2], 'w')
except IOError:
    e = "Can't open output file for writing: " + sys.argv[2]
    print( __file__, ":", e, sys.stderr )
    f = sys.stdout

# subset the components to those wanted in the BOM, controlled
# by <configure> block in kicad_netlist_reader.py
components = net.getInterestingComponents()

# Define the columns
columns = ['SKU', 'Qty']

# Create a new csv writer object to use as the output formatter
out = csv.writer( f, lineterminator='\n', delimiter=',', quotechar='\"', quoting=csv.QUOTE_NONE )

# override csv.writer's writerow() to support encoding conversion (initial encoding is utf8):
def writerow( acsvwriter, columns ):
    utf8row = []
    for col in columns:
        utf8row.append( fromNetlistText( str(col) ) )
    acsvwriter.writerow( utf8row )

row = []

# Get all of the components in groups of matching parts + values
# (see kicad_netlist_reader.py)
grouped = net.groupComponents(components)

writerow( out, ['sku','qty'] )

# Output component information organized by group, aka as collated:
for group in grouped:
    del row[:]

    # Add the reference of every component in the group and keep a reference
    # to the component so that the other data can be filled in once per group
    isResistor = False
    taydaPart = ""

    for component in group:
        taydaPart = component.getField(taydaField)
        if component.getPartName() == "R":
            isResistor = True
            break;

    qty = len(group)

    # Resistors come in 10s so ensure we have a multiple of ten that is enough
    if isResistor:
        qty = 10 + 10 * (qty // 10)

    if len(taydaPart) > 0:
        row.append(taydaPart)
        row.append(qty)
        writerow(out, row)

f.close()
