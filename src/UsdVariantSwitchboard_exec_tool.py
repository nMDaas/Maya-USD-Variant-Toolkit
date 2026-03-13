import os
import sys

def run():
    folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if folder not in sys.path:
        sys.path.append(folder)

    if 'src' in sys.modules:
        del sys.modules['src']
    if 'src.USDVariantSwitchboardToolWrapper' in sys.modules:
        del sys.modules['src.USDVariantSwitchboardToolWrapper']
    import src.USDVariantSwitchboardToolWrapper

    return src.USDVariantSwitchboardToolWrapper.executeVariantSwitchboardTool()