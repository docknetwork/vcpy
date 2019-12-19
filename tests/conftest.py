from typing import List

import pytest

from verifiable_credentials.components import Issuer, Assertion, Recipient, EthereumAnchorHandler


@pytest.fixture
def issuer() -> Issuer:
    yield Issuer(
        name='Chalmers University of Technology',
        url='https://gist.githubusercontent.com/faustow/98db76b26b4d297d0eb98d499e733f77/raw/71f034f76d50fbe8656d6843d72ba1ed42581837/vc_issuer.json',
        email='info@chalmers.se',
        image='',
        revocation_list='https://gist.githubusercontent.com/faustow/07a66855d713409067ff28e10778e2dd/raw/e08bb6d6f1350367d3f6d4f805ab3b1466b584d7/revocation-list-testnet.json',
        public_key='0x472C1a6080a84694990BA2B9a29Ceef672c91d31',
        signature_name='Napoleon Dynamite',
        signature_job_title='President',
        signature_image='',
    )


@pytest.fixture
def assertion() -> Assertion:
    yield Assertion(
        id='2345678901',
        name='Automation and Mechatronics Engineer',
        description='https://www.pluggaz.se/',
        image='',
        narrative='Candidates must be smart.',
    )


@pytest.fixture
def recipients() -> List[Recipient]:
    yield [
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


@pytest.fixture
def eth_anchor_handler() -> EthereumAnchorHandler:
    yield EthereumAnchorHandler(
        node_url='https://ropsten.infura.io/v3/b64e5fd4b1bd4a2b8ed44a32c547c5c7',
        public_key='0x472C1a6080a84694990BA2B9a29Ceef672c91d31',
        private_key='9d8cf7a022b3a033c62aaeb2a2c1973c88777c3f164f861eb22b4db884a4f170',
        key_created_at='2019-03-26T23:37:07.464654+00:00',
    )
