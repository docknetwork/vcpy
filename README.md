![vcpy](docs/assets/vcpy_logo.png)

> Easily issue verifiable credentials (like Blockcerts)
    
![](https://github.com/docknetwork/vcpy/workflows/pytest/badge.svg)

## Table of contents
1. [Background](#background)
1. [Quickstart](#quickstart)
1. [Documentation](#documentation)
1. [Contributing](#contributing)
1. [Contact](#contact)

## Background
There are many kinds of verifiable credentials like W3C's Verifiable Claims, Blockcerts, and others. The goal of `vcpy` is to allow you to easily issue these from your own application!

*Note: this is a WIP, currently only Blockcerts issuing with anchoring to the Ethereum network is provided.* 
 
## Quickstart
Install with:
```bash
pip install vcpy
```

Issue Blockcerts with:
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

And done!

## Documentation
Find our documentation [here](docs/index.md).

## Contributing
1. Fork it (<https://github.com/docknetwork/vcpy/fork>)
1. Create your feature branch (`git checkout -b feature/fooBar`)
1. Commit your changes (`git commit -am 'Add some fooBar'`)
1. Push to the branch (`git push origin feature/fooBar`)
1. Create a new Pull Request

## Contact
This library is maintained by [Fausto Woelflin](https://www.linkedin.com/in/faustowoelflin) at [Dock](https://dock.io).
