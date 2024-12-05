from chromadb import PersistentClient, errors
from tinydb import TinyDB
from tinydb.queries import where

CHROMADB_CLIENT = PersistentClient(path="./.codeas/chromadb")
TINYDB_CLIENT = TinyDB("./.codeas/tinydb.json")


class Storage:
    def store_file_infos_in_tinydb(self, collection_name: str, file_infos: dict):
        table = TINYDB_CLIENT.table(collection_name)
        for filepath, info in file_infos.items():
            doc = {"filepath": filepath, "infos": info}
            table.upsert(doc, where("filepath") == filepath)

    def store_file_infos_in_chromadb(
        self, collection_name: str, file_infos: dict, embeddings: dict
    ):
        try:
            collection = CHROMADB_CLIENT.get_collection(collection_name)
        except errors.InvalidCollectionException:
            collection = CHROMADB_CLIENT.create_collection(collection_name)

        collection.add(
            documents=list(file_infos.values()),
            embeddings=list(embeddings.values()),
            ids=list(file_infos.keys()),
        )

    def fetch_collection_names(self):
        collections = CHROMADB_CLIENT.list_collections()
        return [collection.name for collection in collections]

    def create_collection(self, collection_name: str):
        CHROMADB_CLIENT.create_collection(collection_name)

    def delete_collection(self, collection_name: str):
        CHROMADB_CLIENT.delete_collection(collection_name)

    def fetch_files_in_collection(self, collection_name: str):
        table = TINYDB_CLIENT.table(collection_name)
        return [doc["filepath"] for doc in table.all()]

    def fetch_files_by_paths(self, collection_name: str, filepaths: list[str]):
        table = TINYDB_CLIENT.table(collection_name)
        files_dict = {doc["filepath"]: doc for doc in table.all()}
        return [files_dict[path] for path in filepaths if path in files_dict]

    def query_files_embeddings(
        self, collection_name: str, query_embeddings: list[float], n_results: int = 10
    ):
        collection = CHROMADB_CLIENT.get_collection(collection_name)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)


if __name__ == "__main__":
    storage = Storage()
    print(storage.fetch_collection_names())
