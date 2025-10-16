import magplex
from app_setup import initialize_checks, initialize_worker

app = magplex.create_app()
if __name__ == '__main__':
    initialize_checks()
    initialize_worker()
    app.run(host='0.0.0.0', port=8080, use_reloader=False, debug=False)
