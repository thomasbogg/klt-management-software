from default.settings import LOCAL

if __name__ == '__main__':
    if LOCAL:
        from local import run as local_run
        local_run()
    else:
        from default.update.dates import updatedates
        if not updatedates.is_server_update_hour():
            from libraries.utils import log
            log("Current hour is not within the server update window. Exiting without running the update.")
            quit()
        from server import run as server_run
        server_run()