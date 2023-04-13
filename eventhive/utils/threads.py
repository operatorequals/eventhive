import threading
import queue

class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def join(self, timeout=None):
        self.stop()
        super().join(timeout)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()


class ConsumerDaemon(StoppableThread):
    def __init__(self, consumer_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self._event_queue = queue.Queue()
        self.consumer_func = consumer_func

    def run(self):
        while not self.stopped():
            try:
                item = self._event_queue.get(timeout=0.1)
            except queue.Empty:
                # print("EMPTY QUEUE")
                continue

            args = item['args']
            kwargs = item['kwargs']

            self.consumer_func(*args, **kwargs)

            # print(args, kwargs)
            self._event_queue.task_done()

    def put(self, *args, **kwargs):
        item = {'args':args, 'kwargs':kwargs}
        self._event_queue.put(item)

    def join(self, timeout=None):
        # self._event_queue.join()
        super().join(timeout)


# ec = ConsumerThread(print)
# ec.daemon=True

# ec.put({"event":"hello", "params":{"1":2}})

# ec.put({"event":"hello", "params":{"1":3}})

# ec.start()

# import time; time.sleep(0.01)
# ec.put({"event":"hello", "params":{"1":4}})

# ec.stop()
# # ec.join()