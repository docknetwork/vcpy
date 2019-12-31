import hashlib
from datetime import datetime, timezone

from pycoin.serialize import h2b

from merkletools import MerkleTools


def hash_byte_array(data):
    hashed = hashlib.sha256(data).hexdigest()
    return hashed


def ensure_string(value):
    if isinstance(value, str):
        return value
    return value.decode('utf-8')


class MerkleTree:
    """Representation of a Merkle Tree.

    More at https://en.wikipedia.org/wiki/Merkle_tree.
    """

    def __init__(self):
        self.tree = MerkleTools(hash_type='sha256')

    def populate(self, node_generator) -> None:
        """
        Populate Merkle Tree with data from node_generator. This requires that node_generator yield byte[] elements.
        Hashes, computes hex digest, and adds it to the Merkle Tree
        :param node_generator:
        :return:
        """
        for data in node_generator:
            hashed = hash_byte_array(data)
            self.tree.add_leaf(hashed)

    def get_root(self, binary=False) -> bytearray:
        """
        Finalize tree and return the root, a byte array to anchor on a blockchain tx.
        :return:
        """
        self.tree.make_tree()
        merkle_root = self.tree.get_merkle_root()
        if binary:
            return h2b(ensure_string(merkle_root))
        return ensure_string(merkle_root)

    def get_proof_generator(self, tx_id, signature_type, chain_name) -> dict:
        """
        Returns a generator of Merkle Proofs in insertion order.

        :param tx_id: blockchain transaction id
        :return:
        """
        root = ensure_string(self.tree.get_merkle_root())
        node_count = len(self.tree.leafs)
        for index in range(0, node_count):
            proof = self.tree.get_proof(index)
            proof2 = []

            for p in proof:
                dict2 = dict()
                for key, value in p.items():
                    dict2[key] = ensure_string(value)
                proof2.append(dict2)
            target_hash = ensure_string(self.tree.get_leaf(index))
            merkle_proof = {
                "type": ['MerkleProof2017', 'Extension'],
                "merkleRoot": root,
                "targetHash": target_hash,
                "proof": proof2,
                "anchors": [{
                    "sourceId": tx_id,
                    "type": signature_type,
                    "chain": chain_name
                }]}
            yield merkle_proof


def factor_in_new_try(number, try_count) -> int:
    """Increase the given number with 10% with each try."""
    factor = float(f"1.{try_count}")
    return int(number * factor)


def create_iso8601_tz() -> str:
    """Get the current datetime in ISO 8601 format."""
    ret = datetime.now(timezone.utc)
    return ret.isoformat()


NOW = create_iso8601_tz()
