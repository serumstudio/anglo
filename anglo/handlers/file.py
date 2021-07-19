#               Copyright (c) 2021 Serum Studio.

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This module is used for handling files, watching changes and more.
#: Inherited from https://github.com/samuelcolvin/watchgod/


import os
import re
import logging  
import signal
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from multiprocessing import Process

import asyncio
import functools
from time import time
from enum import IntEnum
from pathlib import Path

from typing import TYPE_CHECKING
from typing import Dict
from typing import Optional
from typing import Pattern
from typing import Set
from typing import Tuple
from typing import Union
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Generator
from typing import cast



logger = logging.getLogger(__name__)

class Change(IntEnum):
    added = 1
    modified = 2
    deleted = 3


if TYPE_CHECKING:
    FileChange = Tuple[Change, str]
    DirEntry   = os.DirEntry[str]
    StatResult = os.stat_result

    FileChanges = Set[FileChange]
    AnyCallable = Callable[..., Any]

class AllWatcher:
    def __init__(self, root_path: Union[Path, str], ignored_paths: Optional[Set[str]] = None) -> None:
        self.files: Dict[str, float] = {}
        self.root_path = str(root_path)
        self.ignored_paths = ignored_paths
        self.check()

    def should_watch_dir(self, entry: 'DirEntry') -> bool:
        return True

    def should_watch_file(self, entry: 'DirEntry') -> bool:
        return True

    def _walk(self, path: str, changes: Set['FileChange'], new_files: Dict[str, float]) -> None:
        if os.path.isfile(path):
            self._watch_file(path, changes, new_files, os.stat(path))
        else:
            self._walk_dir(path, changes, new_files)

    def _watch_file(
        self, path: str, changes: Set['FileChange'], new_files: Dict[str, float], stat: 'StatResult'
    ) -> None:
        mtime = stat.st_mtime
        new_files[path] = mtime
        old_mtime = self.files.get(path)
        if not old_mtime:
            changes.add((Change.added, path))
        elif old_mtime != mtime:
            changes.add((Change.modified, path))

    def _walk_dir(self, dir_path: str, changes: Set['FileChange'], new_files: Dict[str, float]) -> None:
        for entry in os.scandir(dir_path):
            if self.ignored_paths is not None and os.path.join(dir_path, entry) in self.ignored_paths:
                continue

            if entry.is_dir():
                if self.should_watch_dir(entry):
                    self._walk_dir(entry.path, changes, new_files)
            elif self.should_watch_file(entry):
                self._watch_file(entry.path, changes, new_files, entry.stat())

    def check(self) -> Set['FileChange']:
        changes: Set['FileChange'] = set()
        new_files: Dict[str, float] = {}
        try:
            self._walk(self.root_path, changes, new_files)
        except OSError as e:
            # happens when a directory has been deleted between checks
            logger.warning('error walking file system: %s %s', e.__class__.__name__, e)

        # look for deleted
        deleted = self.files.keys() - new_files.keys()
        if deleted:
            changes |= {(Change.deleted, entry) for entry in deleted}

        self.files = new_files
        return changes

class DefaultDirWatcher(AllWatcher):
    ignored_dirs = {'.git', '__pycache__', 'site-packages', '.idea', 'node_modules'}

    def should_watch_dir(self, entry: 'DirEntry') -> bool:
        return entry.name not in self.ignored_dirs


class DefaultWatcher(DefaultDirWatcher):
    ignored_file_regexes = r'\.py[cod]$', r'\.___jb_...___$', r'\.sw.$', '~$', r'^\.\#', r'^flycheck_'

    def __init__(self, root_path: str) -> None:
        self._ignored_file_regexes = tuple(re.compile(r) for r in self.ignored_file_regexes)
        super().__init__(root_path)

    def should_watch_file(self, entry: 'DirEntry') -> bool:
        return not any(r.search(entry.name) for r in self._ignored_file_regexes)


class PythonWatcher(DefaultDirWatcher):
    def should_watch_file(self, entry: 'DirEntry') -> bool:
        return entry.name.endswith(('.py', '.pyx', '.pyd'))


class RegExpWatcher(AllWatcher):
    def __init__(self, root_path: str, re_files: Optional[str] = None, re_dirs: Optional[str] = None):
        self.re_files: Optional[Pattern[str]] = re.compile(re_files) if re_files is not None else re_files
        self.re_dirs: Optional[Pattern[str]] = re.compile(re_dirs) if re_dirs is not None else re_dirs
        super().__init__(root_path)

    def should_watch_file(self, entry: 'DirEntry') -> bool:
        if self.re_files is not None:
            return bool(self.re_files.match(entry.path))
        else:
            return super().should_watch_file(entry)

    def should_watch_dir(self, entry: 'DirEntry') -> bool:
        if self.re_dirs is not None:
            return bool(self.re_dirs.match(entry.path))
        else:
            return super().should_watch_dir(entry)

def unix_ms() -> int:
    return int(round(time() * 1000))


def watch(path: Union[Path, str], **kwargs: Any) -> Generator['FileChanges', None, None]:
    """
    Watch a directory and yield a set of changes whenever files change in that directory or its subdirectories.
    """
    loop = asyncio.new_event_loop()
    try:
        _awatch = awatch(path, loop=loop, **kwargs)
        while True:
            try:
                yield loop.run_until_complete(_awatch.__anext__())
            except StopAsyncIteration:
                break
    except KeyboardInterrupt:
        logger.debug('KeyboardInterrupt, exiting')
    finally:
        loop.close()


class awatch:
    """
    asynchronous equivalent of watch using a threaded executor.
    3.5 doesn't support yield in coroutines so we need all this fluff. Yawwwwn.
    """

    __slots__ = (
        '_loop',
        '_path',
        '_watcher_cls',
        '_watcher_kwargs',
        '_debounce',
        '_min_sleep',
        '_stop_event',
        '_normal_sleep',
        '_w',
        'lock',
        '_executor',
    )

    def __init__(
        self,
        path: Union[Path, str],
        *,
        watcher_cls: Type['AllWatcher'] = DefaultWatcher,
        watcher_kwargs: Optional[Dict[str, Any]] = None,
        debounce: int = 1600,
        normal_sleep: int = 400,
        min_sleep: int = 50,
        stop_event: Optional[asyncio.Event] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._path = path
        self._watcher_cls = watcher_cls
        self._watcher_kwargs = watcher_kwargs or dict()
        self._debounce = debounce
        self._normal_sleep = normal_sleep
        self._min_sleep = min_sleep
        self._stop_event = stop_event
        self._w: Optional['AllWatcher'] = None
        asyncio.set_event_loop(self._loop)
        self.lock = asyncio.Lock()

    def __aiter__(self) -> 'awatch':
        return self

    async def __anext__(self) -> 'FileChanges':
        if self._w:
            watcher = self._w
        else:
            watcher = self._w = await self.run_in_executor(
                functools.partial(self._watcher_cls, self._path, **self._watcher_kwargs)
            )
        check_time = 0
        changes: 'FileChanges' = set()
        last_change = 0
        while True:
            if self._stop_event and self._stop_event.is_set():
                raise StopAsyncIteration()
            async with self.lock:
                if not changes:
                    last_change = unix_ms()

                if check_time:
                    if changes:
                        sleep_time = self._min_sleep
                    else:
                        sleep_time = max(self._normal_sleep - check_time, self._min_sleep)
                    await asyncio.sleep(sleep_time / 1000)

                s = unix_ms()
                new_changes = await self.run_in_executor(watcher.check)
                changes.update(new_changes)
                now = unix_ms()
                check_time = now - s
                debounced = now - last_change
                if logger.isEnabledFor(logging.DEBUG) and changes:
                    logger.debug(
                        '%s time=%0.0fms debounced=%0.0fms files=%d changes=%d (%d)',
                        self._path,
                        check_time,
                        debounced,
                        len(watcher.files),
                        len(changes),
                        len(new_changes),
                    )

                if changes and (not new_changes or debounced > self._debounce):
                    logger.debug('%s changes released debounced=%0.0fms', self._path, debounced)
                    return changes

    async def run_in_executor(self, func: 'AnyCallable', *args: Any) -> Any:
        return await self._loop.run_in_executor(self._executor, func, *args)

    def __del__(self) -> None:
        self._executor.shutdown()


def _start_process(target: 'AnyCallable', args: Tuple[Any, ...], kwargs: Optional[Dict[str, Any]]) -> Process:
    process = Process(target=target, args=args, kwargs=kwargs or {})
    process.start()
    return process


def _stop_process(process: Process) -> None:
    if process.is_alive():
        logger.debug('stopping process...')
        pid = cast(int, process.pid)
        os.kill(pid, signal.SIGINT)
        process.join(5)
        if process.exitcode is None:
            logger.warning('process has not terminated, sending SIGKILL')
            os.kill(pid, signal.SIGKILL)
            process.join(1)
        else:
            logger.debug('process stopped')
    else:
        logger.warning('process already dead, exit code: %d', process.exitcode)


def run_process(
    path: Union[Path, str],
    target: 'AnyCallable',
    *,
    args: Tuple[Any, ...] = (),
    kwargs: Optional[Dict[str, Any]] = None,
    callback: Optional[Callable[[Set['FileChange']], None]] = None,
    watcher_cls: Type['AllWatcher'] = PythonWatcher,
    watcher_kwargs: Optional[Dict[str, Any]] = None,
    debounce: int = 400,
    min_sleep: int = 100,
) -> int:
    """
    Run a function in a subprocess using multiprocessing.Process, restart it whenever files change in path.
    """

    process = _start_process(target=target, args=args, kwargs=kwargs)
    reloads = 0

    try:
        for changes in watch(
            path, watcher_cls=watcher_cls, debounce=debounce, min_sleep=min_sleep, watcher_kwargs=watcher_kwargs
        ):
            callback and callback(changes)
            _stop_process(process)
            process = _start_process(target=target, args=args, kwargs=kwargs)
            reloads += 1
    finally:
        _stop_process(process)
        
    return reloads


async def arun_process(
    path: Union[Path, str],
    target: 'AnyCallable',
    *,
    args: Tuple[Any, ...] = (),
    kwargs: Optional[Dict[str, Any]] = None,
    callback: Optional[Callable[['FileChanges'], Awaitable[None]]] = None,
    watcher_cls: Type['AllWatcher'] = PythonWatcher,
    debounce: int = 400,
    min_sleep: int = 100,
) -> int:
    """
    Run a function in a subprocess using multiprocessing.Process, restart it whenever files change in path.
    """
    watcher = awatch(path, watcher_cls=watcher_cls, debounce=debounce, min_sleep=min_sleep)
    start_process = partial(_start_process, target=target, args=args, kwargs=kwargs)
    process = await watcher.run_in_executor(start_process)
    reloads = 0

    async for changes in watcher:
        callback and await callback(changes)
        await watcher.run_in_executor(_stop_process, process)
        process = await watcher.run_in_executor(start_process)
        reloads += 1

    await watcher.run_in_executor(_stop_process, process)
    return reloads