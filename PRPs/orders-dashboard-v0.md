name: "Orders Dashboard v0 PRP - Comprehensive Implementation Blueprint"
description: |
  Complete implementation guide for building the Orders Dashboard page in Next.js 14 with TanStack Table,
  including all necessary context, patterns, and validation loops for one-pass implementation.

---

## Goal
Build a **complete Orders Dashboard page** for distributors/sellers that displays orders in a sortable, filterable table with bulk selection capabilities and order detail side panel. This is the first feature slice for the Reddi frontend application.

## Why
- **Business value**: Enables distributors to efficiently manage order processing workflow
- **User impact**: Provides overview, inspection, and bulk confirmation capabilities for order management
- **Integration foundation**: Establishes design system, routing, and component patterns for future features
- **Problems solved**: Manual order processing, lack of order visibility, inefficient bulk operations

## What
**User-visible behavior:**
1. **Overview**: Sortable, filterable table showing recent orders with customer info, channels, dates, and status
2. **Inspect**: Click table rows to open side panel with order details (placeholder content for v0)
3. **Bulk confirm**: Select multiple orders via checkboxes and confirm them (console.log for v0)
4. **Search & Filter**: Search orders and filter by status (Pending Review, Accepted)
5. **Responsive**: Table becomes horizontally scrollable on mobile devices

**Technical requirements:**
- Next.js 14 App Router with TypeScript
- Tailwind CSS with custom design tokens
- TanStack Table v8 for data grid functionality
- Lucide React for icons
- Mock data layer for v0
- Pixel-perfect match to design references

### Success Criteria
- [ ] Orders page renders at `/orders` with all table columns (Order #, Customer, Channel, Order Date, Sort By, Products, Order Status)
- [ ] Search input and status filter tabs functional
- [ ] Row selection with master checkbox works
- [ ] Order status badges styled per design tokens
- [ ] Side panel opens on row click with placeholder content
- [ ] Responsive layout works on mobile
- [ ] All validation gates pass (lint, type check, tests)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://nextjs.org/docs/app
  why: Next.js 14 App Router patterns, page.tsx structure, layout conventions
  critical: Understand Server vs Client Components for table interactivity

- url: https://tanstack.com/table/latest/docs/framework/react/examples/basic  
  why: useReactTable hook patterns, column definitions, table rendering
  critical: Row selection and sorting implementation patterns

- url: https://tanstack.com/table/v8/docs/framework/react/examples/sorting
  why: Sorting implementation with getSortedRowModel
  
- url: https://lucide.dev/guide/packages/lucide-react
  why: Icon component patterns, common table icons (Check, Search, ChevronDown)
  critical: Tree-shaking and performance optimization

- file: design/tokens.md
  why: Complete design system including colors, typography, spacing, shadows
  critical: Tailwind config integration, state-success color for status badges

- file: design/references/orders_design_1.png
  why: Main table layout, sidebar navigation, customer avatars, status styling
  
- file: design/references/orders_design_2.png  
  why: Filter components, export modal, bulk selection patterns

- file: CLAUDE.md
  why: Project conventions, file size limits, testing requirements, folder structure
  critical: Front-end rules, Tailwind-only styling, file size < 300 lines
```

### Current Codebase Structure
```bash
/Users/macbook/orderagent/
├── CLAUDE.md                 # Project rules and conventions
├── INITIAL.md               # Feature specification
├── design/
│   ├── tokens.md           # Design system tokens
│   └── references/         # Visual design references
│       ├── orders_design_1.png
│       └── orders_design_2.png
└── PRPs/                   # This PRP location

# Status: Empty project - requires Next.js 14 setup
```

### Desired Codebase Structure After Implementation
```bash
/Users/macbook/orderagent/
├── package.json             # Next.js 14 + dependencies
├── tailwind.config.js       # Custom design tokens integration
├── tsconfig.json           # TypeScript configuration
├── next.config.js          # Next.js configuration
├── app/
│   ├── layout.tsx          # Root layout with Inter font
│   ├── page.tsx            # Root page (can redirect to /orders)
│   └── orders/
│       └── page.tsx        # Main orders dashboard page
├── components/
│   ├── OrderTable.tsx      # TanStack table implementation
│   ├── OrderStatusBadge.tsx # Status badge component
│   ├── OrderDrawer.tsx     # Side panel component
│   └── SearchFilterBar.tsx # Search and filter controls
├── types/
│   └── order.ts           # Order interface and related types
├── lib/
│   └── mockOrders.ts      # Mock data for development
└── tests/
    └── orders.test.tsx    # Basic component tests
```

### Known Gotchas & Library Quirks
```typescript
// CRITICAL: TanStack Table v8 requires stable references
// Example: Use React.useMemo for columns and data to prevent re-renders
const columns = React.useMemo(() => [...], [])
const data = React.useMemo(() => mockOrders, [])

// CRITICAL: Next.js 14 App Router component distinctions
// Table components need "use client" directive for interactivity
"use client"

// CRITICAL: Tailwind custom tokens integration
// Must extend theme in tailwind.config.js with design tokens
theme: {
  extend: {
    colors: {
      brand: { navy: { 900: '#0B0130', 700: '#1C0A53', 50: '#F2F1FA' } },
      state: { success: '#64C09B', warning: '#F5B547', error: '#F16063' }
    }
  }
}

// CRITICAL: Lucide React tree-shaking
// Import only needed icons: import { Search, ChevronDown, Check } from 'lucide-react'

// CRITICAL: TanStack Table column definitions with TypeScript
const columnHelper = createColumnHelper<Order>()
const columns = [
  columnHelper.accessor('id', { header: 'Order #' }),
  columnHelper.accessor('customer.name', { header: 'Customer' })
]
```

## Implementation Blueprint

### Data Models and Structure
```typescript
// types/order.ts - Core data structure
export interface Order {
  id: string;
  customer: {
    name: string;
    avatar: string;
  };
  channel: 'WHATSAPP' | 'SMS' | 'EMAIL';
  orderDate: string;
  products: number;
  status: 'CONFIRMED' | 'PENDING';
}

// Validation: Use exact interface as specified in INITIAL.md
// Pattern: Place in /types/ directory following CLAUDE.md conventions
```

### List of Tasks to be Completed (Implementation Order)

```yaml
Task 1: Project Setup
CREATE package.json via Next.js 14 setup:
  - RUN: npx create-next-app@latest . --ts --tailwind --app --eslint
  - INSTALL: pnpm add @tanstack/react-table lucide-react clsx
  - VERIFY: All dependencies installed correctly

Task 2: Design System Integration  
MODIFY tailwind.config.js:
  - INJECT: Custom color tokens from design/tokens.md
  - ADD: Custom font families, spacing, shadows, border radius
  - PRESERVE: Existing Tailwind defaults
  - PATTERN: Follow exact token structure from design/tokens.md

Task 3: Type Definitions
CREATE types/order.ts:
  - DEFINE: Order interface exactly as specified in INITIAL.md
  - ADD: Additional helper types for filters, sorting
  - PATTERN: Use TypeScript strict mode, export interfaces

Task 4: Mock Data Layer
CREATE lib/mockOrders.ts:
  - GENERATE: 50 sample orders with realistic data
  - MIRROR: Order interface structure exactly
  - INCLUDE: Mix of CONFIRMED/PENDING status, various channels
  - ADD: TODO comments for future Supabase integration

Task 5: Core Page Structure
CREATE app/orders/page.tsx:
  - IMPLEMENT: Main orders dashboard layout
  - INCLUDE: Search bar, filter tabs, table container
  - PATTERN: "use client" directive, proper TypeScript typing
  - STYLE: Match design references pixel-perfectly

Task 6: Table Implementation
CREATE components/OrderTable.tsx:
  - IMPLEMENT: TanStack Table with all required columns
  - ADD: Column sorting, row selection, master checkbox
  - PATTERN: useReactTable hook with proper column definitions
  - STYLE: Tailwind classes only, responsive design

Task 7: Status Badge Component
CREATE components/OrderStatusBadge.tsx:
  - IMPLEMENT: Status indicator with dot + text
  - USE: state-success token for confirmed orders
  - PATTERN: Reusable component with proper typing
  - STYLE: Match design reference exactly

Task 8: Side Panel Component
CREATE components/OrderDrawer.tsx:
  - IMPLEMENT: Slide-out panel for order details
  - CONTENT: Placeholder content for v0
  - PATTERN: Portal-based modal with proper z-index
  - STYLE: shadow-modal, proper animations

Task 9: Search and Filter Bar
CREATE components/SearchFilterBar.tsx:
  - IMPLEMENT: Search input with placeholder
  - ADD: Status filter tabs (Pending Review, Accepted)
  - PATTERN: Controlled components with proper state management
  - STYLE: Match design system exactly

Task 10: Integration and Validation
MODIFY app/orders/page.tsx:
  - INTEGRATE: All components together
  - IMPLEMENT: Bulk selection and console.log confirmation
  - ADD: Click handlers for row selection and side panel
  - TEST: All functionality works as specified
```

### Per Task Pseudocode

```typescript
// Task 6 - OrderTable.tsx Critical Implementation
"use client"
import { useReactTable, createColumnHelper, getCoreRowModel, getSortedRowModel } from '@tanstack/react-table'

export function OrderTable({ orders }: { orders: Order[] }) {
  // PATTERN: Stable references to prevent re-renders
  const data = React.useMemo(() => orders, [orders])
  
  // CRITICAL: Column definitions with proper accessors
  const columnHelper = createColumnHelper<Order>()
  const columns = React.useMemo(() => [
    // Selection column
    columnHelper.display({
      id: 'select',
      header: ({ table }) => (
        <Checkbox 
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
        />
      )
    }),
    // Order ID
    columnHelper.accessor('id', {
      header: 'Order #',
      cell: info => info.getValue()
    }),
    // Customer with avatar
    columnHelper.accessor('customer', {
      header: 'Customer',
      cell: info => (
        <div className="flex items-center space-x-3">
          <img src={info.getValue().avatar} className="w-8 h-8 rounded-full" />
          <span>{info.getValue().name}</span>
        </div>
      )
    }),
    // Status badge
    columnHelper.accessor('status', {
      header: 'Order Status',  
      cell: info => <OrderStatusBadge status={info.getValue()} />
    })
  ], [])

  // PATTERN: useReactTable with required models
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: true,
    // CRITICAL: Proper state management for selection
    state: {
      rowSelection,
      sorting
    },
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting
  })

  return (
    <div className="overflow-x-auto lg:overflow-x-visible">
      <table className="min-w-full divide-y divide-gray-200">
        {/* Table implementation */}
      </table>
    </div>
  )
}
```

### Integration Points
```yaml
ROUTING:
  - pattern: "/app/orders/page.tsx for main dashboard"
  - layout: "Root layout with proper metadata"

STYLING:
  - config: "tailwind.config.js with complete token integration"
  - pattern: "Utility classes only, no inline styles"
  - responsive: "Table scroll on mobile, full layout on desktop"

STATE MANAGEMENT:
  - pattern: "React.useState for local component state"
  - selection: "TanStack Table built-in row selection"
  - filters: "Local state with proper typing"

ICONS:
  - import: "Tree-shaken imports from lucide-react"
  - usage: "Search, ChevronDown, Check icons in components"
```

## Validation Loop

### Level 1: Setup Validation
```bash
# Initial setup verification
npm install  # Install all dependencies
npm run dev  # Verify development server starts
npm run build # Verify production build works

# Expected: No errors, dev server on localhost:3000
```

### Level 2: Type and Style Validation  
```bash
# TypeScript and linting
npx tsc --noEmit  # Type checking
npm run lint      # ESLint validation

# Expected: No TypeScript errors, no linting issues
```

### Level 3: Component Unit Tests
```typescript
// tests/orders.test.tsx - Basic component rendering
import { render, screen } from '@testing-library/react'
import OrdersPage from '../app/orders/page'
import { mockOrders } from '../lib/mockOrders'

test('renders orders table with data', () => {
  render(<OrdersPage />)
  expect(screen.getByText('ORDERS')).toBeInTheDocument()
  expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
})

test('displays order status badges', () => {
  render(<OrdersPage />)
  expect(screen.getByText('Confirmed')).toBeInTheDocument()
})

test('row selection works', () => {
  render(<OrdersPage />)
  const checkboxes = screen.getAllByRole('checkbox')
  expect(checkboxes.length).toBeGreaterThan(0)
})
```

```bash
# Run tests
npm test
# Expected: All tests pass
```

### Level 4: Visual and Functional Validation
```bash
# Start development server
npm run dev

# Manual testing checklist:
# 1. Navigate to http://localhost:3000/orders
# 2. Verify table renders with all columns
# 3. Test search functionality
# 4. Test status filter tabs
# 5. Test row selection and master checkbox
# 6. Test sorting by clicking column headers
# 7. Test side panel opens on row click
# 8. Test bulk confirm button (console.log)
# 9. Test responsive behavior (resize browser)

# Expected: All functionality works as specified
```

## Final Validation Checklist
- [ ] All tests pass: `npm test`
- [ ] No linting errors: `npm run lint`
- [ ] No type errors: `npx tsc --noEmit`
- [ ] Development server runs: `npm run dev`
- [ ] Production build succeeds: `npm run build`
- [ ] Visual design matches references pixel-perfectly
- [ ] All table functionality works (sort, filter, select)
- [ ] Side panel opens with placeholder content
- [ ] Responsive design works on mobile
- [ ] Console.log shows selected orders on bulk confirm
- [ ] Search and filter functionality works
- [ ] Status badges styled correctly with design tokens

---

## Anti-Patterns to Avoid
- ❌ Don't use inline styles - Tailwind classes only per CLAUDE.md
- ❌ Don't create files > 300 lines - Split into smaller components  
- ❌ Don't mock to pass tests - Fix actual implementation issues
- ❌ Don't use unstable references in TanStack Table - Use React.useMemo
- ❌ Don't forget "use client" directive for interactive components
- ❌ Don't hardcode colors - Use design tokens from tailwind.config.js
- ❌ Don't ignore TypeScript errors - Fix them properly
- ❌ Don't skip responsive testing - Verify mobile layout works

**PRP Confidence Score: 9/10** - Comprehensive context provided with complete design system, technical specifications, validation loops, and implementation patterns. High confidence for one-pass implementation success.