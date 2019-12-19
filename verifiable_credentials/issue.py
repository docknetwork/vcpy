# COMPONENTS ============================
import copy
import uuid
from typing import List, Generator, Dict, Tuple

from pyld import jsonld

from .components import Issuer, Assertion, Recipient, AnchorHandler, Blockcert, Batch
from .helpers import MerkleTree, NOW


class BlockcertsBatch(Batch):
    """Representation of a Blockcerts batch.

    When issuing Blockcerts, using batches is the most cost-effective way of doing so since a single transaction is
    needed for potentially many certificates. Instead of anchoring a hash of each certificate in the blockchain, a
    Merkle Tree is created for the batch and its root is the one being anchored. Then the different certificates are
    updated with the Merkle Proof, which basically describes which hashes were needed (along with the hash of the
    current certificate) to finally create the Merkle Root.

    In order to issue a Blockcerts Batch you need to create the following things:
        - An Issuer
        - An Assertion
        - As many Recipients as you need
        - An Anchor Handler

    Once these are created all you need to do to issue a Blockcerts Batch is:

    >>> from verifiable_credentials import issue
    >>> batch = issue.BlockcertsBatch(
    ...     issuer=issuer,
    ...      assertion=assertion,
    ...      recipients=recipients,
    ...      anchor_handler=eth_anchor_handler,
    ... )
    >>> tx_id, final_certs = batch.run()

    This would yield you:
        - A transaction id in `tx_id`, that tells you which transaction in the given blockchain contains the merkle root
        - A list of `final_certs` which are all the final Blockcerts you just issued.

    Note: if you're using this outside of a web service and wish to write the final Blockcerts as individual JSON files
    you could do something like:
    >>> import json
    >>> for id, cert in final_certs.items():
    ...     with open(f"{id}.json", 'w') as this_cert_file:
    ...         this_cert_file.write(json.dumps(cert.to_dict()))

    :param issuer: Issuer object, contains info about who issues the Blockcert
    :param assertion: Assertion object, contains info about what is being claimed by the Issuer about the Recipient
    :param recipient: list of Recipient objects, they contain info about the entities receiving this Blockcert
    :param anchor_handler: AnchorHandler object, handles anchoring to a blockchain and updating the unsigned certs with
    transaction id and merkle proof.
    """

    def __init__(self, issuer: Issuer, assertion: Assertion, recipients: List[Recipient],
                 anchor_handler: AnchorHandler):

        self.issuer = issuer
        self.assertion = assertion
        self.recipients = recipients
        self.anchor_handler = anchor_handler

        self.issued_on = NOW
        self._create_unsigned_certs()

        self.cert_generator = self._get_cert_generator()

        self.merkle_tree_generator = None
        self.merkle_root = None
        self.anchor_tx_id = None
        self.final_certs = None

    def _create_unsigned_certs(self):
        """Compile the different inputs into an unsigned Blockcert."""
        self.unsigned_certs = {}
        for recipient in self.recipients:
            this_id = str(uuid.uuid4())
            self.unsigned_certs[this_id] = Blockcert(
                id=this_id,
                issuer=self.issuer,
                assertion=self.assertion,
                recipient=recipient,
            )

    def _get_cert_generator(self) -> Generator:
        """Return a generator of jsonld-normalized unsigned certs."""
        for uid, cert in self.unsigned_certs.items():
            normalized = jsonld.normalize(cert.to_dict(), {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
            yield normalized.encode('utf-8')

    def _add_proof_to_certs(self) -> Dict:
        """Add merkle proof to each of the certificates."""
        proof_generator = self.merkle_tree_generator.get_proof_generator(
            self.anchor_tx_id,
            self.anchor_handler.signature_field,
            self.anchor_handler.chain_name
        )
        signed_certs = copy.deepcopy(self.unsigned_certs)
        for _, cert in signed_certs.items():
            proof = next(proof_generator)
            cert.proof = proof
        return signed_certs

    def run(self) -> Tuple[str, Dict]:
        # Input validation is made by each component's init method, so it will fail before getting here.
        # 1- Create merkle tree
        self.merkle_tree_generator = MerkleTree()
        self.merkle_tree_generator.populate(self.cert_generator)
        self.merkle_root = self.merkle_tree_generator.get_root()

        self.anchor_tx_id = self.anchor_handler.anchor(
            self.merkle_tree_generator.get_root(binary=True)
        )
        self.final_certs = self._add_proof_to_certs()
        return self.anchor_tx_id, self.final_certs
