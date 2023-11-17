from connect_unix import connect_unix_socket
from src import app

if __name__ == "__main__":
    connect_unix_socket()
    app.run(host="127.0.0.1", port=8080, debug=True)