from __future__ import print_function

import sys
import numpy as np
import time

from io_shared import NumpyShare


def main():
    N = 150000
    cloud = np.empty((N, 4), dtype=np.float32)
    size = cloud.nbytes

    cloud_share = NumpyShare('/py27_to_py37', '5M', 'put')
    label_share = NumpyShare('/py37_to_py27', '5M', 'get')

    start = time.time()
    for i in range(100):
        cloud_share.put(cloud)
        label = label_share.get()
        assert (cloud == label).all()
    end = time.time()
    print(end - start)


if __name__ == '__main__':
    main()
