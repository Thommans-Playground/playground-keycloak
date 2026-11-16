# 03 - Security Practices

> **What this is.** The defences this product relies on and the reasoning behind them, so a design can be
> checked against them (`/vbench:v-2-design` does this in its constitution check). Keep it to what is actually
> in place; list the rest under *Pending hardening*.

## Defence in depth

(The principle: no single control is trusted alone. Name the layers: edge, application, data, operations.)

## Practices in place

| Practice | What it protects | Where it lives |
|---|---|---|
| (for example: authentication on every route unless allow-listed) | (the threat it addresses) | (module or ADR) |

## Principle of least privilege

(Which credentials, tokens and roles are scoped, and to what.)

## Secrets

(Where secrets live, how they reach the process, what must never be committed or logged.)

## Pending hardening

| Gap | Risk | Trigger to address |
|---|---|---|
| (what is not yet done) | (what could go wrong) | (the event that makes it worth doing) |

## References

(Standards and advisories this follows.)
