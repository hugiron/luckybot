import multiprocessing as mp


class PoolActor:
    def __init__(self, actor, pool_size=None, *args, **kwargs):
        self.pool = [actor.start(pool=self, *args, **kwargs)
                     for i in range(pool_size if pool_size else mp.cpu_count())]
        self.pool_size = len(self.pool)

    def __call__(self, *args, **kwargs):
        return min(self.pool, key=lambda x: x.actor_inbox.qsize())

    def tell(self, message):
        self.__call__().tell(message)

    def ask(self, message, block=True, timeout=None):
        return self.__call__().ask(message, block, timeout)

    def proxy(self):
        return self.__call__().proxy()
