# @[copyright_header]@
"""
Source build event using Gerrit
"""

from typing import Dict

from buildjob import BuildJob
from common import log_error, subdict
from eventsrc import EventSource
from jobscheduler import JobScheduler
from gerrit import Gerrit


class GerritBuildJob(BuildJob):
    """
    Class encapsulating a build job generated through gerrit stream-events
    command
    """
    def __init__(self, gerrit: Gerrit, gerrit_event: dict):
        project = gerrit_event['change']['project']
        change = gerrit_event['patchSet']['revision']

        git_url = 'ssh://{}@{}:{:d}/{}'.format(gerrit.username,
                                               gerrit.hostname,
                                               int(gerrit.port),
                                               project)
        opts = {}
        if gerrit.keyfile:
            opts['git_ssh_cmd'] = 'ssh -i ' + gerrit.keyfile

        super().__init__(project=project,
                         url=git_url,
                         refspec=change,
                         clone_opts=opts)
        self.gerrit_instance = gerrit
        self.gerrit_change = change

    def notify_result(self, success: bool, message: str = None):
        self.gerrit_instance.review(self.project, self.gerrit_change, message)


def _trigger_build(event):
    """
    test whether an event is a merge event, or a manual trigger
    """
    try:
        evttype = event['type']
        if evttype not in ('change-merged', 'comment-added'):
            return (False, False)

        if evttype == 'change-merged':
            return (True, True)

        comment = event['comment']

        if 'MMPACK_UPLOAD_BUILD' in comment:
            return (True, True)

        if 'MMPACK_BUILD' in comment:
            return (True, False)

    except KeyError:
        pass

    return (False, False)


class GerritEventSource(EventSource):
    """
    Class representing an event source spawning event from gerrit streamed
    events
    """
    def __init__(self, scheduler: JobScheduler, config=Dict[str, str]):
        """
        Initialize a Gerrit based event source

        Args:
            @scheduler: scheduler to which job must be added
            @config: dictionary configuring the connection to gerrit. Allowed
                keys are 'hostname', 'username', 'port' and 'keyfile'
        """
        super().__init__(scheduler)
        cfg = subdict(config, ['hostname', 'username', 'port', 'keyfile'])
        self.gerrit_instance = Gerrit(**cfg)

    def _handle_gerrit_event(self, event: dict):
        do_build, do_upload = _trigger_build(event)
        if not do_build:
            return

        job = GerritBuildJob(self.gerrit_instance, event)
        job.do_upload = do_upload
        self.add_job(job)

    def run(self):
        self.gerrit_instance.startWatching()

        while True:
            try:
                event = self.gerrit_instance.getEvent()
            except Exception as err:  # pylint: disable=broad-except
                # an error occurred, but NOT one involving package
                # generation just let slide, it may be caused by a hiccup
                # in the infrastructure.
                log_error('ignoring exception {}'.format(str(err)))
                continue

            self._handle_gerrit_event(event)
