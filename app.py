from Pulsse import pulsse_app


app = pulsse_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
