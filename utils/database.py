import os
from dotenv import load_dotenv

from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ.get("DATABASE_URL"))

db = client.KnightBot

guilds_db = db.Guilds
