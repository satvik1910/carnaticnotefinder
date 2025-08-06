import os

class ConfigOverride:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ragnotefinder_new.db'
    
# Override the database URI
from config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///ragnotefinder_new.db'
