import magplex
from app_setup import initialize, run_scheduler

app = magplex.create_app()
if __name__ == '__main__':
    initialize()
    run_scheduler()
    app.run(host='0.0.0.0', port=8080, use_reloader=True, debug=True)

