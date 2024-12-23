import uuid

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

    def create_collection(self, repo_path: str):
        collection_name = self.get_collection_name(repo_path)
        CHROMADB_CLIENT.create_collection(collection_name)

    def delete_collection(self, repo_path: str):
        collection_name = self.get_collection_name(repo_path)
        CHROMADB_CLIENT.delete_collection(collection_name)

    def fetch_files_in_collection(self, repo_path: str):
        collection_name = self.get_collection_name(repo_path)
        table = TINYDB_CLIENT.table(collection_name)
        return [doc["filepath"] for doc in table.all()]

    def fetch_files_by_paths(self, repo_path: str, filepaths: list[str]):
        collection_name = self.get_collection_name(repo_path)
        table = TINYDB_CLIENT.table(collection_name)
        files_dict = {doc["filepath"]: doc for doc in table.all()}
        return [files_dict[path] for path in filepaths if path in files_dict]

    def query_files_embeddings(
        self, repo_path: str, query_embeddings: list[float], n_results: int = 10
    ):
        collection_name = self.get_collection_name(repo_path)
        collection = CHROMADB_CLIENT.get_collection(collection_name)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)

    def get_collection_name(self, repo_path: str):
        """Convert path to valid chroma db collection name using UUID"""
        namespace = uuid.NAMESPACE_URL
        return str(uuid.uuid5(namespace, repo_path))


if __name__ == "__main__":
    storage = Storage()
    print(storage.fetch_collection_names())
