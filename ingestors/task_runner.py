import logging
import threading

from servicelayer import settings
from servicelayer.queue import poll_task, mark_task_finished

from ingestors.manager import Manager

log = logging.getLogger(__name__)


class TaskRunner(object):
    """A long running task runner that uses Redis as a task queue"""

    @classmethod
    def execute(cls, dataset, entity, context):
        manager = Manager(dataset, context)
        file_path = manager.get_filepath(entity)
        manager.ingest(file_path, entity)

    @classmethod
    def process(cls):
        for task in poll_task():
            # log.info("Received Task: ", str(task))
            if task is None:
                return
            dataset, entity, context = task
            try:
                cls.execute(*task)
            except Exception as exc:
                log.exception("Task failed to execute:", exc)
            finally:
                mark_task_finished(dataset)

    @classmethod
    def run(cls):
        log.info("Processing queue (%s threads)", settings.INGESTOR_THREADS)
        threads = []
        for i in range(settings.INGESTOR_THREADS):
            t = threading.Thread(target=cls.process)
            t.daemon = True
            t.start()
            threads.append(t)
        # stop workers
        for t in threads:
            t.join()
