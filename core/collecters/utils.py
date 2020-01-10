import time
import threading
import traceback


def set_interval(f, args, interval):
    class StoppableThread(threading.Thread):

        def __init__(self, f, args, interval):
            threading.Thread.__init__(self)
            self.f = f
            self.args = args
            self.interval = interval
            self.stop_execution = False
            self.daemon = True

        def run(self):
            while not self.stop_execution:
                before = time.time()
                try:
                    self.f(*self.args)
                except:
                    traceback.print_exc()
                    print("Something bad happened here :-(")
                    pass
                execution_duration = time.time() - before
                time_to_wait = self.interval - execution_duration
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

        def stop(self):
            self.stop_execution = True

    t = StoppableThread(f, args, interval)
    t.start()
    return t