# Anchor SDK

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/anchorco/anchor-sdk)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Control what your AI agents store. Audit everything.**

_Block_ bad data before storage.

_Prove_ what happened.

_Rollback_ when things break.


## Installation

**Python:** ```pip install anchorai```

**TypeScript/JavaScript:** ```npm install anchorai```

## Quick Start

### 1. Sign Up and Get Credentials

1. **Go to [app.getanchor.dev](https://getanchor.dev)**
2. **Sign up** with your email (or log in if you already have an account)
3. **Copy your API Key** (e.g., `anc_abc123...`)
4. **Important:** Save this securely - you won't be able to see the API key again!

### 2. Install the SDK

**Python** ([PyPI](https://pypi.org/project/anchorai/1.1.0/), [code](https://github.com/anchorco/anchor-sdk/python-sdk)):
```python
from anchor import Anchor

# Initialize with your API key
anchor = Anchor(api_key="your-api-key")

# Create an agent
agent = anchor.agents.create("support-bot")

# Configure policies
anchor.config.update(agent.id, {"policies": {"block_pii": True}})
```

**TypeScript** ([npm](https://www.npmjs.com/package/anchorai/1.1.0), [code](https://github.com/anchorco/anchor-sdk)):
```typescript
import { Anchor } from 'anchorai';

// Initialize with your API key
const anchor = new Anchor({ 
  apiKey: 'your-api-key'
});

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

## Documentation

[**API Documentation**](https://docs.getanchor.dev)

[Python Reference](https://github.com/anchorco/anchor-sdk/tree/release/v1.1.0/python-sdk)
  
[TypeScript Reference](typescript-sdk/README.md)
  
**Contributing**: Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**License**: This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links
- Website: **https://getanchor.dev**
- Docs: **https://docs.getanchor.dev**
- GitHub Issues: https://github.com/anchorco/anchor-sdk/issues
- Support: founders@getanchor.dev
