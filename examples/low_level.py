import io_shared
from io_shared import UnsafeSharedMMap, SharedMMap, RWSharedMMap

# --- UnsafeSharedMMap
data = b'Hello, World!!!'
shm = UnsafeSharedMMap('/my_share', 15)
shm.write(data)
shm.seek(0)
print(shm.readline())  # 'Hello, World!!!\n'
shm.close()

# --- SharedMMap
data = b'Hello, World!!!'
shm = SharedMMap('/my_share', 15)
try:
    shm.write(data)
except io_shared.WriteAccessError as e:
    print('Oops')
with shm.lock():
    shm.write(data)

shm.seek(0)

try:
    print(shm.readline())
except io_shared.ReadAccessError as e:
    print('Oops')
with shm.lock():
    print(shm.readline())  # 'Hello, World!!!\n'

# --- RWSharedMMap
data = b'Hello, World!!!'
shm = RWSharedMMap('/my_share', 15)
with shm.lock_write():
    shm.write(data)

shm.seek(0)

with shm.lock_read():
    print(shm.readline())  # 'Hello, World!!!\n'