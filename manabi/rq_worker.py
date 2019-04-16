import rq


class ManabiWorker(rq.Worker):
    def __init__(self, *args, **kwargs):
        super(ManabiWorker, self).__init__(*args, **kwargs)
