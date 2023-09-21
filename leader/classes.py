from typing import List
import logging

from pydatatask import (
    FileRepositoryBase,
    FileRepository,
    DirectoryRepository,
    Task,
    KubeTask,
)

log = logging.getLogger("operator")


class MountpointMixin(FileRepositoryBase):
    def __init__(self, mountpoint, suffix, extension="", case_insensitive=False):
        super().__init__(
            mountpoint / suffix, extension=extension, case_insensitive=case_insensitive
        )
        self.mountpoint = mountpoint
        self.suffix = suffix

    def info(self, job):
        suffix = self.suffix / (job + self.extension)
        return MountpointInfo(self.mountpoint, suffix)


class MountpointFileRepository(FileRepository, MountpointMixin):
    pass


class MountpointDirectoryRepository(DirectoryRepository, MountpointMixin):
    pass


class MountpointInfo:
    def __init__(self, mountpoint, suffix):
        self.mountpoint = mountpoint
        self.suffix = suffix

    def __str__(self):
        return str(self.mountpoint / self.suffix)


class CreateOutdirOnStartMixin(Task):
    def __init__(self, *args, output: DirectoryRepository, output_name: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.__output = output
        self.link(output_name, output, is_output=True)

    async def launch(self, job):
        await self.__output.mkdir(job)
        await super().launch(job)


class RunOnTimeoutMixin(KubeTask):
    def __init__(self, *args, script: List[str], **kwargs):
        super().__init__(*args, **kwargs)
        self.__script = script

    async def handle_timeout(self, pod):
        exec_stream = await self.podman.v1_ws.connect_get_namespaced_pod_exec(
            pod.metadata.name,
            self.podman.namespace,
            command=self.__script,
            stderr=True,
            stdout=True,
            stdin=False,
            tty=False,
        )
        if exec_stream:
            log.error(exec_stream)


class Phase2(RunOnTimeoutMixin, CreateOutdirOnStartMixin, KubeTask):
    pass


class Phase2b(CreateOutdirOnStartMixin, KubeTask):
    pass


class Phase3(CreateOutdirOnStartMixin, KubeTask):
    pass
