from default.settings import LOCAL

if __name__ == '__main__':
    if LOCAL:
        from local import main as local_main
        local_main()
    else:
        from server import main as server_main
        server_main()