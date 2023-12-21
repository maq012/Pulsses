from Pulsse import pulsse_app


app = pulsse_app()


if __name__ == "__main__":
    app.run(debug=False, port=5000, threaded=True)
