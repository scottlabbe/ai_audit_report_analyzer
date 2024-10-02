from flask_migrate import Migrate
from flask_script import Manager
from main import app, init_db

manager = Manager(app)
migrate = Migrate(app, init_db())

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
