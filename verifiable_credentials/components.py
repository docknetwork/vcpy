from abc import ABC, abstractmethod

from attrdict import AttrDict
from web3 import Web3

from .helpers import NOW, factor_in_new_try


class Issuer:
    """A basic version of an Issuer as defined by the Blockcerts standard.

    More at: https://github.com/IMSGlobal/cert-schema/blob/master/cert_schema/2.0/issuerSchema.json

    :param name: Name of the issuer
    :param url: Url to the issuer's public profile (must resolve to a valid jsonld)
    :param email: Email to contact the issuer
    :param image: base64-encoded PNG or SVG that represents the issuer (a logo for example)
    :param revocation_list: Url to the issuer's public revocation list (must resolve to a valid jsonld)
    :param public_key: Public key owned by the issuer (or authorized to issue on their behalf).
    :param signature_name: (optional) Name of the person signing the certificate
    :param signature_job_title: (optional) Title of the person signing the certificate
    :param signature_image: (optional) base64-encoded PNG or SVG that represents the signature of the person signing.

    Note: All three of signature_name, signature_job_title and signature_image must exist in order for the signature
    section to be added to the Blockcert.
    """

    def __init__(
            self: str,
            name: str,
            url: str,
            email: str,
            image: str,
            revocation_list: str,
            public_key: str,
            signature_name: str = "",
            signature_job_title: str = "",
            signature_image: str = ""
    ):
        self.name = name
        self.url = url
        self.email = email
        self.image = image
        self.revocation_list = revocation_list
        self.public_key = public_key
        self.signature_name = signature_name
        self.signature_job_title = signature_job_title
        self.signature_image = signature_image


class Assertion:
    """A basic version of an Assertion as defined by the Blockcerts standard.

    More at https://github.com/IMSGlobal/cert-schema/blob/master/cert_schema/2.0/schema.json

    :param id: id of the assertion
    :param name: name of the assertion
    :param description: description of the assertion
    :param image: base64-encoded PNG or SVG that represents the assertion (a logo for example)
    :param narrative: narrative of the assertion
    :param display_html: (optional) valid HTML that will be displayed when validating in public validators
    """

    def __init__(self, id: str, name: str, description: str, image: str, narrative: str, display_html: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.image = image
        self.narrative = narrative
        self.display_html = display_html


class Recipient:
    """A basic version of a Recipient as defined by the Blockcerts standard.

    More at https://github.com/IMSGlobal/cert-schema/blob/master/cert_schema/2.0/recipientSchema.json

    :param name: name of the recipient
    :param email: email of the recipient
    :param public_key: public key of the recipient
    :param email_hashed: is the email hashed?
    """

    def __init__(self, name: str, email: str, public_key: str, email_hashed: bool = False):
        self.name = name
        self.email = email
        self.public_key = public_key
        self.email_hashed = email_hashed


class AnchorHandler(ABC):
    """Common interface for anchoring mechanisms.

    :param chain_name: name of the chain, for now one of 'ethereumMainnet' or 'ethereumRopsten', in the future at least
    'bitcoinMainnet', 'bitcoinRegtest' and 'bitcoinTestnet' should be added.
    :param signature_field: transaction field where the merkle root will be posted. For now only 'ETHData' will work, in
    the future at least 'BTCOpReturn' should be added.
    """

    def __init__(self, chain_name: str):
        raise NotImplementedError

    @abstractmethod
    def anchor(self, data) -> str:
        """Anchor the given data to a Blockchain transaction.

        :param data: data to be stored in a transaction, usually this is a merkle root but it may be a single hash if
        the batch being issued consists of a single certificate.
        :return: reference to the anchor, like a transaction id
        """
        raise NotImplementedError


class EthereumAnchorHandler(AnchorHandler):
    """Use the Ethereum blockchain to anchor.

    :param node_url: url to an Ethereum node (can also be a 3rd party service url as Infura)
    :param public_key: Public key to use to sign the transaction (the personal account must be funded)
    :param private_key: Public key to use to sign the transaction (the personal account must be funded)
    :param key_created_at: Ethereum account creation date.
    :param max_retry: (optional) Amount of allowed retries if the anchoring operation fails
    :param gas_price: (optional) desired gas price for the anchoring transaction
    :param gas_limit: (optional) desired gas limit for the anchoring transaction
    :param account_to: (optional) desired destination of the anchoring transaction
    :param chain_name: (optional) one of ethereumRopsten or ethereumMainnet
    """
    signature_field = 'ETHData'

    def __init__(
            self,
            node_url: str,
            public_key: str,
            private_key: str,
            key_created_at: str,
            max_retry: int = 3,
            gas_price: int = 20000000000,
            gas_limit: int = 25000,
            account_to: str = '0xdeaDDeADDEaDdeaDdEAddEADDEAdDeadDEADDEaD',
            chain_name: str = 'ethereumRopsten'
    ):
        self.node_url = node_url
        self.private_key = private_key
        self.public_key = public_key
        self.key_created_at = key_created_at
        self.max_retry = max_retry
        self.gas_price = gas_price
        self.gas_limit = gas_limit
        self.web3 = Web3(Web3.HTTPProvider(self.node_url))
        self.account_to = account_to
        self.chain_name = chain_name

    def _get_signed_tx(self, merkle_root: str, gas_price: int, gas_limit: int, try_count: int) -> AttrDict:
        """Prepare a raw transaction and sign it with the private key."""
        nonce = self.web3.eth.getTransactionCount(self.public_key)
        tx_info = {
            'nonce': nonce,
            'to': self.account_to,
            'value': 0,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'data': merkle_root,
        }
        if try_count:
            tx_info['nonce'] = tx_info['nonce'] + try_count
            tx_info['gas'] = factor_in_new_try(tx_info['gas'], try_count)
            tx_info['gasPrice'] = factor_in_new_try(tx_info['gasPrice'], try_count)
        signed_tx = self.web3.eth.account.sign_transaction(tx_info, self.private_key)
        return signed_tx

    def _ensure_balance(self) -> None:
        """Make sure that the Ethereum account's balance is enough to cover the tx costs."""
        assert self.web3.eth.getBalance(self.public_key) >= self.gas_limit * self.gas_price

    def anchor(self, merkle_root) -> str:
        """Store the merkle root as data in an Ethereum transaction and return the tx id."""
        for i in range(self.max_retry):
            assert self.web3.isConnected()
            self._ensure_balance()
            signed_tx = self._get_signed_tx(merkle_root, self.gas_price, self.gas_limit, i)
            try:
                tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                tx_id = self.web3.toHex(tx_hash)
                return tx_id
            except Exception as e:
                if i >= self.max_retry - 1:
                    raise
                continue


class Blockcert:
    """A basic version of a Blockcert as defined by the standard.

    More at:
        - https://github.com/IMSGlobal/cert-schema/blob/master/cert_schema/2.0/
        - http://www.imsglobal.org/sites/default/files/Badges/OBv2p0Final/index.html


    :param id: unique id of this specific Blockcert
    :param issuer: Issuer object, contains info about who issues the Blockcert
    :param assertion: Assertion object, contains info about what is being claimed by the Issuer about the Recipient
    :param recipient: Recipient object, contains info about the entity receiving this Blockcert
    """

    def __init__(self, id: str, issuer: Issuer, assertion: Assertion, recipient: Recipient):
        self.id = id
        self.issuer = issuer
        self.assertion = assertion
        self.recipient = recipient
        self.anchor_tx_id = None
        self.proof = None

    def to_dict(self) -> dict:
        """Get a dictionary representation of a Blockcert."""
        raw_dict = {
            "@context": [
                "https://w3id.org/openbadges/v2",
                "https://w3id.org/blockcerts/v2",
                {
                    "displayHtml": {
                        "@id": "schema:description"
                    }
                }
            ],
            "type": "Assertion",
            "issuedOn": NOW,
            "id": "urn:uuid:" + self.id,
            "recipient": {
                "type": "email",
                "identity": self.recipient.email,
                "hashed": self.recipient.email_hashed
            },
            "recipientProfile": {
                "type": [
                    "RecipientProfile",
                    "Extension"
                ],
                "name": self.recipient.name,
                "publicKey": "ecdsa-koblitz-pubkey:" + self.recipient.public_key
            },
            "badge": {
                "type": "BadgeClass",
                "id": "urn:uuid:" + self.assertion.id,
                "name": self.assertion.name,
                "description": self.assertion.description,
                "image": self.assertion.image,
                "issuer": {
                    "id": self.issuer.url,
                    "type": "Profile",
                    "name": self.issuer.name,
                    "url": self.issuer.url,
                    "email": self.issuer.email,
                    "image": self.issuer.image,
                    "revocationList": self.issuer.revocation_list
                },
                "criteria": {
                    "narrative": self.assertion.narrative
                }
            },
            "verification": {
                "type": [
                    "MerkleProofVerification2017",
                    "Extension"
                ],
                "publicKey": "ecdsa-koblitz-pubkey:" + self.issuer.public_key
            }
        }
        if self.assertion.display_html:
            raw_dict["displayHtml"] = self.assertion.display_html,
        if self.issuer.signature_image and self.issuer.signature_job_title and self.issuer.signature_name:
            raw_dict['signatureLines'] = [
                {
                    "type": [
                        "SignatureLine",
                        "Extension"
                    ],
                    "jobTitle": self.issuer.signature_job_title,
                    "image": self.issuer.signature_image,
                    "name": self.issuer.signature_name
                }
            ]
        if self.proof:
            raw_dict['signature'] = self.proof

        return raw_dict


class Batch(ABC):
    """Common interface for batching operations."""

    @abstractmethod
    def run(self):
        """Execute all the ordererd steps to create a batch of final certificates."""
        raise NotImplementedError
