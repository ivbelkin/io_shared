import posix_ipc
import mmap
import numpy as np


class UnsafeSharedMMap(mmap.mmap):

    def __new__(cls, name, size):
        size = cls._size_to_bytes(size)
        memory = posix_ipc.SharedMemory(name=name, size=size, flags=posix_ipc.O_CREAT)
        obj = super(UnsafeSharedMMap, cls).__new__(cls, memory.fd, memory.size)
        memory.close_fd()
        return obj

    def __init__(self, name, size):
        self.name = name
    
    @staticmethod
    def _size_to_bytes(size):
        multipliers = {'K': 2**10, 'M': 2**20, 'G': 2**30}
        if isinstance(size, str):
            return int(size[:-1]) * multipliers[size[-1]]
        elif isinstance(size, int):
            return size
    
    def resize(self, *args, **kwargs):
        raise NotImplementedError
    
    def __del__(self):
        try:
            self.close()
            memory = posix_ipc.SharedMemory(self.name)
            memory.unlink()
        except posix_ipc.ExistentialError:
            pass


class SharedMMap(UnsafeSharedMMap):

    def __init__(self, name, size):
        super(SharedMMap, self).__init__(name, size)

        self._sem = posix_ipc.Semaphore(name=name, initial_value=1, flags=posix_ipc.O_CREAT)
        self._aquire_on_enter = False
        self._cm = False
    
    def find(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).find(*args, **kwargs)
        else:
            raise ReadAccessError

    def flush(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).flush(*args, **kwargs)
        else:
            raise WriteAccessError

    def move(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).move(*args, **kwargs)
        else:
            raise WriteAccessError
    
    def read(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).read(*args, **kwargs)
        else:
            raise ReadAccessError

    def read_byte(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).read_byte(*args, **kwargs)
        else:
            raise ReadAccessError

    def readline(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).readline(*args, **kwargs)
        else:
            raise ReadAccessError

    def rfind(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).rfind(*args, **kwargs)
        else:
            raise ReadAccessError

    def write(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            try:
                return super(SharedMMap, self).write(*args, **kwargs)
            except ValueError as e:
                if str(e) == 'data out of range':
                    raise OOMError
        else:
            raise WriteAccessError
    
    def write_byte(self, *args, **kwargs):
        if self._cm and self._aquire_on_enter:
            return super(SharedMMap, self).write_byte(*args, **kwargs)
        else:
            raise WriteAccessError
    
    def __enter__(self):
        self._cm = True
        if self._aquire_on_enter:
            self._sem.acquire()
            return self
        else:
            return super(SharedMMap, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise
        self._cm = False
        if self._aquire_on_enter:
            self._sem.release()
            self.lock_on_enter = False
            return self
        else:
            return super(SharedMMap, self).__exit__(exc_type, exc_val, exc_tb)

    def lock(self):
        self._aquire_on_enter = True
        return self

    def __del__(self):
        try:
            self._sem.unlink()
        except posix_ipc.ExistentialError:
            pass
        super(SharedMMap, self).__del__()
        

class RWSharedMMap(UnsafeSharedMMap):

    def __init__(self, name, size, max_readers=1000):
        super(RWSharedMMap, self).__init__(name, size)
        self.max_readers = max_readers

        self._sem_write = posix_ipc.Semaphore(name=name + '_write', initial_value=1, flags=posix_ipc.O_CREAT)
        self._aquire_write_on_enter = False

        self._sem_read = posix_ipc.Semaphore(name=name + '_read', initial_value=max_readers, flags=posix_ipc.O_CREAT)
        self._aquire_read_on_enter = False

        self._cm = False
    
    def find(self, *args, **kwargs):
        if self._cm and self._aquire_read_on_enter:
            return super(RWSharedMMap, self).find(*args, **kwargs)
        else:
            raise ReadAccessError

    def flush(self, *args, **kwargs):
        if self._cm and self._aquire_write_on_enter:
            return super(RWSharedMMap, self).flush(*args, **kwargs)
        else:
            raise WriteAccessError

    def move(self, *args, **kwargs):
        if self._cm and self._aquire_write_on_enter:
            return super(RWSharedMMap, self).move(*args, **kwargs)
        else:
            raise WriteAccessError
    
    def read(self, *args, **kwargs):
        if self._cm and self._aquire_read_on_enter:
            return super(RWSharedMMap, self).read(*args, **kwargs)
        else:
            raise ReadAccessError

    def read_byte(self, *args, **kwargs):
        if self._cm and self._aquire_read_on_enter:
            return super(RWSharedMMap, self).read_byte(*args, **kwargs)
        else:
            raise ReadAccessError

    def readline(self, *args, **kwargs):
        if self._cm and self._aquire_read_on_enter:
            return super(RWSharedMMap, self).readline(*args, **kwargs)
        else:
            raise ReadAccessError

    def rfind(self, *args, **kwargs):
        if self._cm and self._aquire_read_on_enter:
            return super(RWSharedMMap, self).rfind(*args, **kwargs)
        else:
            raise ReadAccessError

    def write(self, *args, **kwargs):
        if self._cm and self._aquire_write_on_enter:
            try:
                return super(RWSharedMMap, self).write(*args, **kwargs)
            except ValueError as e:
                if str(e) == 'data out of range':
                    raise OOMError
        else:
            raise WriteAccessError
    
    def write_byte(self, *args, **kwargs):
        if self._cm and self._aquire_write_on_enter:
            return super(RWSharedMMap, self).write_byte(*args, **kwargs)
        else:
            raise WriteAccessError
    
    def __enter__(self):
        self._cm = True
        if self._aquire_write_on_enter:
            self._sem_write.acquire()
            while self._sem_read.value < self.max_readers:
                pass
            return self
        elif self._aquire_read_on_enter:
            self._sem_write.acquire()
            self._sem_read.acquire()
            self._sem_write.release()
        else:
            return super(RWSharedMMap, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise
        self._cm = False
        if self._aquire_write_on_enter:
            self._sem_write.release()
            self._aquire_write_on_enter = False
            return self
        elif self._aquire_read_on_enter:
            self._sem_read.release()
            self._aquire_read_on_enter = False
            return self
        else:
            return super(RWSharedMMap, self).__exit__(exc_type, exc_val, exc_tb)

    def lock_write(self):
        self._aquire_write_on_enter = True
        return self
    
    def lock_read(self):
        self._aquire_read_on_enter = True
        return self

    def __del__(self):
        try:
            self._sem_write.unlink()
            self._sem_read.unlink()
        except posix_ipc.ExistentialError:
            pass
        super(RWSharedMMap, self).__del__()


class NumpyShare(object):

    def __init__(self, name, size, mode):
        self.name = name
        self.size = size
        self.mode = mode

        self._shm = SharedMMap(name, size)
        self._sem = posix_ipc.Semaphore(name=name + '_np', initial_value=0, flags=posix_ipc.O_CREAT)
    
    def put(self, arr):
        if self.mode == 'put':
            with self._shm.lock():
                self._shm.seek(0)
                np.save(self._shm, arr)
            if self._sem.value == 0:
                self._sem.release()
        elif self.mode == 'get':
            raise WriteAccessError('Writing(put) to memory is not allowed in "get" mode')

    def get(self):
        if self.mode == 'get':
            self._sem.acquire()
            with self._shm.lock():
                self._shm.seek(0)
                return np.load(self._shm)
        elif self.mode == 'put':
            raise WriteAccessError('Reading(get) from memory is not allowed in "put" mode')
    
    def __del__(self):
        try:
            self._sem.unlink()
        except posix_ipc.ExistentialError:
            pass


class OOMError(Exception):

    def __init__(self, message='Out of shared memory! Try increase size'):
        super(OOMError, self).__init__(message)


class WriteAccessError(Exception):

    def __init__(self, message='Write to memory without lock is not permitted'):
        super(WriteAccessError, self).__init__(message)


class ReadAccessError(Exception):

    def __init__(self, message='Read from memory without lock is not permitted'):
        super(ReadAccessError, self).__init__(message)
