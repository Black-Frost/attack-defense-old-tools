def mapping_origin_dest(origin_dest):
    # TODO: Create Challenge class
    host, port = origin_dest
    if port == 5555:
        return ("172.31.137.66", 5555), "3o3"
    if port == 6666:
        return ("172.31.137.66", 6666), "ratio"
    if port == 7777:
        return ("172.31.137.66", 7777), "db"
    if port == 8888:
        return ("172.31.137.66", 8888), "hello"
    if port == 9999:
        return ("172.31.137.66", 9999), "vm"
    return (host, port), 'others'
