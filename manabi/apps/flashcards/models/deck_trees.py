class TreeItem(object):
    def __init__(self, *args, **kwargs):
        self.deck = None
        self.deck_collection = None


class DeckTreeItem(TreeItem):
    def __init__(self, deck):
        super(DeckTreeItem, self).__init__()
        self.deck = deck


class DeckCollectionTreeItem(TreeItem):
    def __init__(self, collection):
        super(DeckCollectionTreeItem, self).__init__()
        self.deck_collection = collection
