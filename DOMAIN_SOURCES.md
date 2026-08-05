# Production domain sources

This file defines the only repositories authorized to deploy the current Stargate domains.

| Domain | Source of truth | Deployment |
|---|---|---|
| `www.stargateedu.co.kr` and apex | `DongsooJung/dongsoojung.github.io` | GitHub Pages / current site workflow |
| `portal.stargateedu.co.kr` | `DongsooJung/stargate-main` | GitHub Pages |
| `blog.stargateedu.co.kr` | `DongsooJung/stargate-blog-hub` | GitHub Pages and repository Actions |
| `shop.stargateedu.co.kr` | `DongsooJung/stargateedu-shop` | GitHub Pages / current shop workflow |

## Rules

1. Make production changes only in the repository listed above.
2. Do not deploy a `repos/*` snapshot or `mirror/*` branch to a production repository.
3. Legacy repositories may redirect to the current service but must not contain an independently maintained production copy.
4. Secrets belong in repository or deployment-provider secret stores, never in committed files.
5. A repository migration requires updating this file, the target repository policy, and the Notion repository dashboard in the same change window.

## Legacy mapping

- `stargate.github.io` → legacy Stargate site
- `stargate-blog` → replaced by `stargate-blog-hub`
- `stargate-shop` → replaced by `stargateedu-shop`

Last reviewed: 2026-08-05.
