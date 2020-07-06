import sys
import numpy as np
import time

from io_shared import NumpyShare


def main():
    N = 150000
    cloud = np.empty((N, 4), dtype=np.float32)
    size = cloud.nbytes

    cloud_share = NumpyShare('/py27_to_py37', '5M', 'get')
    label_share = NumpyShare('/py37_to_py27', '5M', 'put')

    start = time.time()
    put_times, get_times = [], []
    for i in range(100):
        time.sleep(0.1)
        t1 = time.perf_counter()
        cloud = cloud_share.get()
        t2 = time.perf_counter()
        get_times.append(t2 - t1)

        label = cloud

        time.sleep(0.1)
        t1 = time.perf_counter()
        label_share.put(label)
        t2 = time.perf_counter()
        put_times.append(t2 - t1)

    end = time.time()
    print(end - start)
    put_times = np.array(put_times[1:])
    get_times = np.array(get_times[1:])
    print('put', np.mean(put_times), np.std(put_times), np.min(put_times), np.max(put_times), (size / 2**27 / put_times).mean(), 'Gb/s')
    print('get', np.mean(get_times), np.std(get_times), np.min(get_times), np.max(get_times), (size / 2**27 / get_times).mean(), 'Gb/s')


if __name__ == '__main__':
    main()
