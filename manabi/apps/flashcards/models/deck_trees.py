# def build_tree(decks):
#     '''
#     Assumes `select_related('collection')` has been applied to `decks`.
#     '''
#     collections = {}
#     for deck in decks.iterator():
#         if deck.collection_id is None:
#             continue
#         collections[deck.collection_id] = deck.collection


class TreeItem(object):
    def __init__(self, *args, **kwargs):
        self.deck = None
        self.collection = None


class DeckTreeItem(TreeItem):
    def __init__(self, deck):
        super(DeckTreeItem, self).__init__()
        self.deck = deck


class DeckCollectionTreeItem(TreeItem):
    def __init__(self, collection):
        super(CollectionTreeItem, self).__init__()
        self.collection = collection
