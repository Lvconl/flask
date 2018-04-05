from ajax import ajax
from models import app
from models import db

views = __import__('views')
app.register_blueprint(ajax)

if __name__ == '__main__':
    db.create_all()
    app.run()
