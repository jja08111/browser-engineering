from layout import BlockLayout, DisplayList, DocumentLayout

def paint_tree(layout_object: DocumentLayout | BlockLayout,
               display_list: DisplayList):
  display_list.extend(layout_object.paint())

  for child in layout_object.children:
    paint_tree(child, display_list)
