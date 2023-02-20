import pymongo

client = pymongo.MongoClient("mongodb://192.168.2.5:27017/")
db = client["walletrank"]
col = db["nodes"]


def get_db_content(name: str) -> dict | None:
    return col.find_one({"_id": name})

def set_db_content(obj: dict) -> str:
    return col.insert_one(obj).inserted_id
