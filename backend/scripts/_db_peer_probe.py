from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    print('db_uri_host=', uri.split('@')[-1].split('/')[0].split(':')[0])
    print('db_uri_db=', uri.rstrip('/').split('/')[-1])
    print('server_current_database=', db.session.execute(text('select current_database()')).scalar())
    print('schema=', db.session.execute(text('select current_schema()')).scalar())
    print('table_exists=', db.session.execute(text("select to_regclass('public.job_applications')")).scalar())
