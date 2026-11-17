# Repository snapshots and deployment governance

> This repository is the profile and documentation hub. It is **not** the deployment source for the four production domains.

## Production sources of truth

| Domain | Canonical repository | Editing rule |
|---|---|---|
| `www.stargateedu.co.kr` / apex | [DongsooJung/dongsoojung.github.io](https://github.com/DongsooJung/dongsoojung.github.io) | Edit only in the canonical repository |
| `portal.stargateedu.co.kr` | [DongsooJung/stargate-main](https://github.com/DongsooJung/stargate-main) | Edit only in the canonical repository |
| `blog.stargateedu.co.kr` | [DongsooJung/stargate-blog-hub](https://github.com/DongsooJung/stargate-blog-hub) | Edit only in the canonical repository |
| `shop.stargateedu.co.kr` | [DongsooJung/stargate-shop-redirect](https://github.com/DongsooJung/stargate-shop-redirect) | Edit only in the canonical repository while the custom domain is attached there |

`DongsooJung/stargateedu-shop` is a **staged replacement**, not the current production source. A future migration requires an explicit custom-domain and GitHub Pages cutover plus a same-window update of `DOMAIN_SOURCES.md` and the repository dashboard.

The folders under `repos/` are reference snapshots, consolidation material, or reusable packages. They must not overwrite production repositories.

## Snapshot branches

`scripts/sync-mirrors.sh` may create `mirror/*` branches inside this repository for comparison and recovery. Automatic cross-repository deployment has been removed. The protected production targets are explicitly denied by `scripts/deploy-mirrors.sh`.

## Legacy repositories

| Repository | Status | Current replacement or operating source |
|---|---|---|
| `stargate.github.io` | Legacy candidate; not archived | `stargate-main` or `dongsoojung.github.io`, depending on content |
| `stargate-blog` | Legacy candidate; not archived | `stargate-blog-hub` |
| `stargate-shop` | Legacy candidate; not archived | `stargate-shop-redirect` |

Legacy status in this document does not itself archive a repository. Verify Pages, CNAME, Actions, external integrations, and recovery needs before changing repository state.

See [DOMAIN_SOURCES.md](../DOMAIN_SOURCES.md) for the operating policy and [ARCHIVED_REPOS.md](../ARCHIVED_REPOS.md) for the current consolidation status.
