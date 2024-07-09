import queue


class EventManager:
    _instance = None
    _queue = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._queue = queue.Queue()
        return cls._instance

    @property
    def queue(self):
        return self._queue

    def put(self, event):
        self._queue.put(event)

    def get(self, block=True, timeout=None):
        return self._queue.get(block, timeout)

    def empty(self):
        return self._queue.empty()
