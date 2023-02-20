from typing import Any, Mapping

import pymongo

client = pymongo.MongoClient("mongodb://192.168.2.5:27017/")
db = client["walletrank"]


def get_db_content(name: str, collection: str) -> Mapping[str, Any] | None:
    col = db[collection]
    db_result = col.find_one({"_id": name})
    if db_result:
        db_result['name'] = db_result['_id']
        return db_result
    return None


def set_db_content(obj: dict, collection: str):
    col = db[collection]
    col.update_one({"_id": obj['name']}, {"$set": obj}, upsert=True)
