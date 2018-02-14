from models import app


views = __import__('views')

if __name__ == '__main__':
    app.run()
