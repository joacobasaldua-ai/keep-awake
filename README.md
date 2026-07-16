# Retiro de productos

A Next.js (App Router + Tailwind CSS) recreation of a mobile product-pickup flow: select products to withdraw, swipe to confirm at the counter, and see a success screen once the pickup is registered.

## Screens

- **Mis productos** — list of pending products with a "select all" toggle and per-item checkboxes.
- **Retiro** — order summary with a swipe-to-confirm control ("Retirado").
- **Loading** — brief confirmation state while the pickup is processed.
- **Success** — confirmation screen with an option to go back to the product list.

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view it.

## Customizing

- Product data lives in `src/lib/data.ts`.
- Screens are split into components under `src/components/`.
- The app name shown on the loading screen is the `appName` constant in `src/lib/data.ts`.

## Deploy on Vercel

Push this repository to GitHub and import it in [Vercel](https://vercel.com/new) — no extra configuration is required.
