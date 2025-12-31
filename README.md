# Anchor SDK

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
![Build Status](https://img.shields.io/github/actions/workflow/status/anchorco/anchor-sdk/ci.yml?branch=main)
![npm](https://img.shields.io/npm/v/anchorai)
![pip](https://img.shields.io/pypi/v/anchorai)

**Control what your AI agents store. Audit everything.**

_Block_ bad data before storage. _Prove_ what happened. _Rollback_ when things break.

## Installation

**Python:** ```pip install anchorai```

**TypeScript/JavaScript:** ```npm install anchorai```

## Quick Start

### 1. Get an API Key

Sign up at [getanchor.dev](https://getanchor.dev) to get your API key and workspace ID.

### 2. Start Using Anchor

**Python** ([PyPI](https://pypi.org/project/anchorai), [code](https://github.com/anchorco/anchor-sdk/tree/main/python-sdk)):
```python
from anchor import Anchor

anchor = Anchor(api_key="your-api-key")

agent = anchor.agents.create("support-bot")
anchor.config.update(agent.id, {"policies": {"block_pii": True}})
```

**TypeScript** ([NPM](https://www.npmjs.com/package/anchorai), [code](https://github.com/anchorco/anchor-sdk/tree/main/typescript-sdk)):
```typescript
import { Anchor } from 'anchorai';

const anchor = new Anchor({ apiKey: 'your-api-key' });

const agent = await anchor.agents.create('support-bot');
await anchor.config.update(agent.id, { policies: { block_pii: true } });
```

| Namespace | Purpose | API coverage |
|-----------|-----------|-----------|
| `anchor.agents` | Manage agents | create, get, list, update, delete, suspend, activate|
| `anchor.config` | Version configurations |get, update, versions, get version, rollback|
| `anchor.data` | Store data with policy enforcement |write, read, read full, delete, delete prefix, list, search|
| `anchor.checkpoints` | Create state snapshots and restore |create, list, get, restore, delete|
| `anchor.audit` | Keep hash-chained audit trail |query, get, verify, export|

## Docs

https://docs.getanchor.dev/
  
**Contributing**: Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**License**: This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links

- **Website**: https://getanchor.dev
- **GitHub Issues**: https://github.com/anchorco/anchor-sdk/issues
- **Available** at (click):
<p>
  <a href="https://pypi.org/project/anchorai/">
    <img
      src="assets/pip_icon.png"
      width="200"
      alt="PyPI package"
    />
  </a>
  <a href="https://www.npmjs.com/package/anchorai">
    <img
      src="assets/npm_icon.png"
      width="200"
      alt="NPM package"
    />
  </a>
</p>

- **Support**: founders@getanchor.dev
