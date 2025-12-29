from app_core import create_dash_app

app = create_dash_app()

if __name__ == "__main__":
    app.run(debug=True)