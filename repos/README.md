# Repository snapshots and deployment governance

> This repository is the profile and documentation hub. It is **not** the deployment source for the four production domains.

## Production sources of truth

| Domain | Canonical repository | Editing rule |
|---|---|---|
| `www.stargateedu.co.kr` / apex | [DongsooJung/dongsoojung.github.io](https://github.com/DongsooJung/dongsoojung.github.io) | Edit only in the canonical repository |
| `portal.stargateedu.co.kr` | [DongsooJung/stargate-main](https://github.com/DongsooJung/stargate-main) | Edit only in the canonical repository |
| `blog.stargateedu.co.kr` | [DongsooJung/stargate-blog-hub](https://github.com/DongsooJung/stargate-blog-hub) | Edit only in the canonical repository |
| `shop.stargateedu.co.kr` | [DongsooJung/stargateedu-shop](https://github.com/DongsooJung/stargateedu-shop) | Edit only in the canonical repository |

The folders under `repos/` are reference snapshots, consolidation material, or reusable packages. They must not overwrite production repositories.

## Snapshot branches

`scripts/sync-mirrors.sh` may create `mirror/*` branches inside this repository for comparison and recovery.  
Automatic cross-repository deployment has been removed. The protected production targets are explicitly denied by `scripts/deploy-mirrors.sh`.

## Legacy repositories

| Repository | Status | Replacement |
|---|---|---|
| `stargate.github.io` | Legacy | `stargate-main` or `dongsoojung.github.io` |
| `stargate-blog` | Legacy | `stargate-blog-hub` |
| `stargate-shop` | Legacy | `stargateedu-shop` |

See [DOMAIN_SOURCES.md](../DOMAIN_SOURCES.md) for the full operating policy.
