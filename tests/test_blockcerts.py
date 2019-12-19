from verifiable_credentials import issue


def test_issuing(issuer, assertion, recipients, eth_anchor_handler):
    batch = issue.BlockcertsBatch(
        issuer=issuer,
        assertion=assertion,
        recipients=recipients,
        anchor_handler=eth_anchor_handler,
    )
    tx_id, final_certs = batch.run()
    assert tx_id
    assert len(final_certs.keys()) == len(recipients)

    # import json
    # for id, cert in final_certs.items():
    #     with open(f"{id}.json", 'w') as this_cert_file:
    #         this_cert_file.write(json.dumps(cert.to_dict()))
    for id, cert in final_certs.items():
        assert cert.proof['anchors'][0]['sourceId'] == tx_id
        assert cert.proof['merkleRoot'] == batch.merkle_root
