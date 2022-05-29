import time

if __name__ == '__main__':
    li = [i for i in range(10 ** 7)]
    di = {i: i for i in range(10 ** 7)}

    t0 = time.time()
    print(-1 in li)
    t1 = time.time()
    print(f"time elapsed: {t1 - t0}s")

    t0 = time.time()
    print(-1 in di)
    # print(-1 in list(di.keys()))
    t1 = time.time()
    print(f"time elapsed: {t1 - t0}s")