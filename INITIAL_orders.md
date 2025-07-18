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

- **Data layer → dummy only**  
  - Crea `/lib/mockOrders.ts` que exporte `const orders: Order[] = […]`.

- **Type safety**  
  - Define `/types/order.ts` con la interfaz:  
    ```ts
    export interface Order {
      id: string;
      customer: { name: string; avatar: string };
      channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
      orderDate: string;      // ISO
      products: number;       // total items
      status: 'CONFIRMED' | 'PENDING';
    }
    ```

- **Folder structure (obligatorio)**  
/app/orders/page.tsx
/components/OrderTable.tsx
/components/OrderStatusBadge.tsx
/components/OrderDrawer.tsx (placeholder)
/lib/mockOrders.ts
/types/order.ts

- **Styling → solo Tailwind**  
- Agrega los tokens de `design/tokens.md` a `tailwind.config.js`.  
- Prohibido usar estilos inline o CSS modules.

- **Accesibilidad**  
- Checkboxes con `aria-label`.  
- Filas deben ser focus-able (`tabIndex={0}`).

- **Future hooks**  
- Coloca comentarios `// TODO Supabase` y `// TODO ERP` donde apliquen; no implementes integración real.

- **Lint / Format**  
- Usa la configuración ESLint + Prettier generada por `create-next-app`.


*Commit message suggestion*:  
`feat: Orders dashboard v0 with mock data & design tokens`

## Setup prerequisite
If the project is empty, run:
`npx create-next-app@latest . --ts --tailwind --app --eslint`
and then `pnpm add @tanstack/react-table lucide-react clsx`.