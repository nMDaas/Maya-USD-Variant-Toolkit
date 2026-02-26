# Maya tool which allows users to easily and quickly place objects in/around another object 
# with a set radius and many other customizable parameters.

# Instructions: Make any changes to the path desired and run this file.

import sys

#SET THIS FOLDER to the parent folder that you've downloaded the repository to
#or ensure that the parent folder is added to your PYTHONPATH
folder = '/Users/natashadaas/USD_Switchboard'

#check if folder is part of PYTHONPATH and if not, add it
if folder not in sys.path:
    sys.path.append(folder)

if 'src' in sys.modules:
    del sys.modules['src']
if 'src.VariantAuthoringToolWrapper' in sys.modules:
    del sys.modules['src.VariantAuthoringToolWrapper']
import src.VariantAuthoringToolWrapper

window = src.VariantAuthoringToolWrapper.executeModelVariantAuthor()