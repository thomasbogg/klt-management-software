from default.settings import LOCAL

if __name__ == '__main__':
    if LOCAL:
        from local import run as local_run
        local_run()
    else:
        from server import run as server_run
        server_run()