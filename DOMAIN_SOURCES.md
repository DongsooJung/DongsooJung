# Production domain sources

This file defines the only repositories authorized to deploy the current Stargate domains.

| Domain | Source of truth | Deployment |
|---|---|---|
| `www.stargateedu.co.kr` and apex | `DongsooJung/dongsoojung.github.io` | GitHub Pages / current site workflow |
| `portal.stargateedu.co.kr` | `DongsooJung/stargate-main` | GitHub Pages |
| `blog.stargateedu.co.kr` | `DongsooJung/stargate-blog-hub` | GitHub Pages and repository Actions |
| `shop.stargateedu.co.kr` | `DongsooJung/stargate-shop-redirect` | GitHub Pages from `main` (current live source) |

## Rules

1. Make production changes only in the repository listed above.
2. Do not deploy a `repos/*` snapshot or `mirror/*` branch to a production repository.
3. Legacy repositories may redirect to the current service but must not contain an independently maintained production copy.
4. While the shop custom domain remains attached to `DongsooJung/stargate-shop-redirect`, treat `DongsooJung/stargateedu-shop` as a staged replacement rather than a production deployment source.
5. Secrets belong in repository or deployment-provider secret stores, never in committed files.
6. A repository migration requires updating this file, the target repository policy, and the Notion repository dashboard in the same change window.

## Staged replacement

- `DongsooJung/stargateedu-shop` contains a prepared storefront and payment implementation, but its GitHub Pages deployment is inactive and it is not authorized to deploy `shop.stargateedu.co.kr` until the custom-domain and Pages migration is explicitly completed.

## Legacy mapping

- `stargate.github.io` → legacy Stargate site
- `stargate-blog` → replaced by `stargate-blog-hub`
- `stargate-shop` → replaced by `stargateedu-shop`

Last verified: 2026-09-20.
