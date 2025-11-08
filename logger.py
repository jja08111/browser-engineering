from layout import BlockLayout, DocumentLayout
from html_parser import Node

def print_tree(node: Node | BlockLayout | DocumentLayout, indent=0):
  print(" " * indent, node)
  for child in node.children:
    print_tree(child, indent + 2)
