# INITIAL.md – Orders Page v0 (Reddi)

<!--
This file kicks off the first feature slice for the Reddi frontend.
Only ONE screen (Orders) will be built in this PR.
-->

## Feature

**Orders Dashboard**

Build the **Orders** page that lists all orders for a distributor, praticularily, this is the seller dashboard.

User goals:

1. **Overview** – View a sortable, filterable table of recent orders.
2. **Inspect** – Click a row to open a side-panel with line-items (stub for now).
3. **Bulk confirm** – Select one or more orders and hit *Confirm Orders* (just `console.log`).

### Functional spec

| Element                    | Details                                                                   |
|----------------------------|---------------------------------------------------------------------------|
| Table columns              | *Order #, Customer avatar + name, Channel, Order Date, Sort By, Products, Order Status* |
| Search + status filter bar | Search input (`placeholder="Search..."`) & Tabs (`Pending Review`, `Accepted`) |
| Row selection              | Checkbox far left; master checkbox in header                              |
| Order status badge         | Dot + text (green “Confirmed”) – use `state-success` token                |
| Pagination                 | Not required – show first 50 mocked rows                                  |
| Side-panel modal           | Create component `<OrderDrawer />` but keep placeholder content           |
| Responsiveness             | Table becomes horizontally scrollable below `lg` breakpoint               |

### Visual spec

* Pixel-match **orders_design_1.png** + **orders_design_2.png** stored at  
  `design/references/`.
* Palette, spacing, radii, shadows, etc. defined in **design/tokens.md**.

## Examples (folder)
## Documentation (RAG Sources)

1. **Next.js 14 App Router** – <https://nextjs.org/docs/app>
2. **Tailwind CSS** – <https://tailwindcss.com/docs>
3. **TanStack Table v8** – <https://tanstack.com/table/v8>
4. **Lucide Icons** – <https://lucide.dev>
5. **design/tokens.md** – authoritative design tokens for Reddi  
6. **design/references/** – pixel reference PNGs

## Other Considerations / Gotchas

| Area          | Constraint / Tip                                                                                 |
|---------------|--------------------------------------------------------------------------------------------------|
| Data layer    | **Dummy only**: import from `/lib/mockOrders.ts`. Place file in this PR.                         |
| Types         | Create `/types/order.ts` with interface:<br>```ts<br>export interface Order { id:string; customer:{name:string; avatar:string}; channel:'WHATSAPP'|'SMS'|'EMAIL'; orderDate:string; products:number; status:'CONFIRMED'|'PENDING'; }``` |
| Folder layout | Must follow:<br>`/app/orders/page.tsx` → main screen<br>`/components/OrderTable.tsx`, `OrderStatusBadge.tsx`, etc.<br>`/lib/` for data fetchers |
| Styling       | Use **Tailwind classes** only; no inline styles. Add new tokens to `tailwind.config.js` per `design/tokens.md`. |
| Accessibility | Table rows keyboard-navigable; checkboxes have `aria-label`.                                     |
| Future hook   | Add `// TODO:` comments where Supabase fetch or ERP push will later plug in.                     |
| ESLint/Prettier| Respect repo defaults (if not present, use Next.js 14 default).                                  |

---

*Commit message suggestion*:  
`feat: Orders dashboard v0 with mock data & design tokens`

## Setup prerequisite
If the project is empty, run:
`npx create-next-app@latest . --ts --tailwind --app --eslint`
and then `pnpm add @tanstack/react-table lucide-react clsx`.