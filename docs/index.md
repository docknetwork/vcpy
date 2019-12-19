# vcpy

vcpy is an easy-to-use Python library to issue verifiable credentials. 

There are many kinds of verifiable credentials like W3C's Verifiable Claims, Blockcerts, and others. The goal of `vcpy` is to allow you to easily issue these from your own application!

*Note: this is a WIP, currently only Blockcerts issuing with anchoring to the Ethereum network is provided.*  
    
## Table of contents

1. [Why](#Why)
2. [Status](#Status)
3. [How to issue Blockcerts](#How-to-issue-Blockcerts)
4. [Creating the required components](#Creating-the-required-components) <br>
4.1 [Issuer](#Issuer)<br>
4.2 [Assertion](#Assertion)<br>
4.3 [Recipients](#Recipients)<br>
4.4 [Anchor handler](#Anchor-handler)<br>


## Why 
Although useful as PoCs, current implementations of verifiable credentials-issuing software projects suffer one or more of the following issues: 
- race conditions
- imposibility to use as part of a larger application
- overengineered code that makes it hard to contribute to

`vcpy` tries to improve user adoption by providing a better user experience, and to encourage open source contributions by using simpler code and good documentation.
Because Clean Code is better than fancy code.


## Status
- [ ] Blockcerts issuing: 
  - [x] Batch issuing
  - [x] Anchor to Ethereum blockchain
  - [ ] Anchor to Bitcoin, Polkadot or other blockchains
  - [ ] Additional global fields
  - [ ] Additional per-recipient fields
- [ ] VCDMv1 issuing
  - [ ] Blockcerts-wrapping
  - [ ] Credential signing
- [ ] Remote schema validation ?
- [ ] More tests

--- 

## How to issue Blockcerts
When issuing Blockcerts, using batches is the most cost-effective way of doing so since a single transaction is needed for potentially many certificates. Instead of anchoring a hash of each certificate in the blockchain, a Merkle Tree is created for the batch and its root is the one being anchored. Then the different certificates are updated with the Merkle Proof, which basically describes which hashes were used (along with the hash of the current certificate) to finally create a Merkle Tree with the anchored Merkle Root.

In order to issue a Blockcerts Batch you need to create the following things:
- An Issuer
- An Assertion
- As many Recipients as you want
- An Anchor Handler

Once these are created all you need to do to issue a Blockcerts Batch is:
```python
from verifiable_credentials import issue
batch = issue.BlockcertsBatch(
    issuer=issuer,
     assertion=assertion,
     recipients=recipients,
     anchor_handler=eth_anchor_handler,
)
tx_id, final_certs = batch.run()
```

And that's it! There you have:
- A transaction id in `tx_id`, that tells you which transaction in the given blockchain contains the merkle root
- A list of `final_certs` (python dictionaries) which are all the final Blockcerts you just issued.

### Creating the required components
Currently there's a basic implementation of all required models, let us examine them in the following sections.

#### Issuer
The Issuer model represents a basic version of an `Issuer` as defined by the Blockcerts standard, and contains info about who issues the Blockcert. All the required parameters are strings and are quite self explanatory but here's a summary:
- `name`: Name of the issuer
- `url`: Url to the issuer's public profile (must resolve to a valid jsonld)
- `email`: Email to contact the issuer
- `image`: base64-encoded PNG or SVG that represents the issuer (a logo for example)
- `revocation_list`: Url to the issuer's public revocation list (must resolve to a valid jsonld)
- `public_key`: Public key owned by the issuer (or authorized to issue on their behalf).
- `signature_name`: (optional) Name of the person signing the certificate
- `signature_job_title`: (optional) Title of the person signing the certificate
- `signature_image`: (optional) base64-encoded PNG or SVG that represents the signature of the person signing.

Note: All three of signature_name, signature_job_title and signature_image must exist in order for the signature
section to be added to the Blockcert.

Here's an example of what this looks like: 
```python
from verifiable_credentials.components import Issuer
issuer = Issuer(
    name='Chalmers University of Technology',
    url='https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json',
    email='info@chalmers.se',
    image='',
    revocation_list='https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json',
    public_key='0x472...',
    signature_name='Napoleon Dynamite',
    signature_job_title='President',
    signature_image='',
)
```

#### Assertion
The Assertion model represents basic version of an `Assertion` or `claim` as defined by the Blockcerts standard, it contains info about what is being claimed by the Issuer about the Recipient. All the required parameters are strings and are quite self explanatory but here's a summary:
- `id`: id of the assertion, usually a UUID4
- `name`: name of the assertion, like a title for the achievement or what's being claimed about the recipient
- `description`: description of the assertion
- `image`: base64-encoded PNG or SVG that represents the assertion (a logo for example)
- `narrative`: criteria narrative of the assertion
- `display_html`: (optional) valid HTML that will be displayed when validating in public validators


```python
from verifiable_credentials.components import Assertion
assertion = Assertion(
    id='2345678901',
    name='Automation and Mechatronics Engineer',
    description='https://www.pluggaz.se/',
    image='',
    narrative='Candidates must be smart.',
)
```

#### Recipients
The Recipient model represents a basic version of a `recipient` as defined by the Blockcerts standard, it contains info about the entity receiving a given Blockcert. All the required parameters are strings, and are quite self explanatory but here's a summary:
- `name`: name of the recipient
- `email`: email of the recipient
- `public_key`: public key of the recipient
- `email_hashed`: (optional `Bool`) is the email hashed?

```python
from verifiable_credentials.components import Recipient
recipients = [
    Recipient(
        name='Fausto Woelflin',
        email='fausto@dock.io',
        public_key='3456789012',
    ),
    Recipient(
        name='Eddie Vedder',
        email='ed@pearljam.net',
        public_key='4567890123',
    ),
    Recipient(
        name='Thomas Shellby',
        email='tom@shellbylimited.com',
        public_key='5678901234',
    ),
]
```

#### Anchor Handler
An Anchor Handler is an interface for anchoring mechanisms, basically it handles anchoring to a blockchain and updating the unsigned certs with transaction id and merkle proof. All the required parameters are strings, and here's what they mean:

- `chain_name`: name of the chain, for now one of 'ethereumMainnet' or 'ethereumRopsten', in the future at least
'bitcoinMainnet', 'bitcoinRegtest' and 'bitcoinTestnet' should be added.
- `signature_field`: transaction field where the merkle root will be posted. For now only 'ETHData' will work, in
the future at least 'BTCOpReturn' should be added.
```python
from verifiable_credentials.components import EthereumAnchorHandler
anchor_handler = EthereumAnchorHandler(
    node_url='https://ropsten.infura.io/v3/...',
    public_key='0x...',
    private_key='...',
    key_created_at='2019-03-26T23:37:07.464654+00:00',
)
```

