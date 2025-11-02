import magplex
from app_setup import initialize


app = magplex.create_app()
if __name__ == '__main__':
    initialize()
    app.run(host='0.0.0.0', port=8000, use_reloader=True, debug=True)

