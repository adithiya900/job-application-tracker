import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from extensions import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes('job_applications')
    for idx in indexes:
        print(idx['name'], idx['column_names'])
