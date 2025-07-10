# Reddi Design Tokens
Version: 0.1  (derived from Choco-style “Orders” screen)

## 1. Color Palette
| Token            | Hex      | Usage                                     |
|------------------|----------|-------------------------------------------|
| `brand-navy-900` | **#0B0130** | Sidebar background, active nav accent   |
| `brand-navy-700` | #1C0A53  | Sidebar hover / secondary dark surfaces   |
| `brand-navy-50`  | #F2F1FA  | Light tint for selected rows / badges     |
| `primary-ink`    | **#000000** | H1 titles (“ORDERS”)                    |
| `text-default`   | #1A1A1A | Normal body text                          |
| `text-muted`     | #6B6B6B | Placeholder, table secondary labels       |
| `surface-0`      | **#FFFFFF** | Card & table background                |
| `surface-alt`    | #F7F7F7 | Table header row, filters bar            |
| `border-subtle`  | #E4E4E4 | Divider lines, table grid                |
| `state-success`  | **#64C09B** | Green status dot “Confirmed”            |
| `state-warning`  | #F5B547 | Possible future: “Pending”                |
| `state-error`    | #F16063 | Possible future: “Rejected / Error”       |
| `highlight-1`    | #6F56FF | (Thin purple outline you see on screenshot border) |

> _Note_: `brand-navy-900` was sampled at RGB ≈ (11, 1, 48).  
> `state-success` was sampled at RGB ≈ (100, 192, 155).

## 2. Typography
| Token             | Font Family | Weight | Size (rem) | Line-height |
|-------------------|-------------|--------|------------|-------------|
| `font-heading-xl` | "Inter"     | 900    | 3.0rem (≈48px) | 1.125      |
| `font-body-lg`    | "Inter"     | 600    | 1.125rem (18px)| 1.4        |
| `font-body`       | "Inter"     | 400    | 1.0rem  (16px)| 1.5        |
| `font-caption`    | "Inter"     | 400    | 0.875rem (14px)| 1.45      |

- **Letter-spacing**: keep default (tight letter tracking only on headings if needed).
- **Rendering**: use `font-antialiased` utility in Tailwind for clear headings.

## 3. Spacing Scale  (Tailwind style)
| Token | px | Purpose                          |
|-------|----|----------------------------------|
| `space-0` | 0   | None                         |
| `space-1` | 4   | Inner icon padding, checkboxes |
| `space-2` | 8   | Row gap, micro-paddings      |
| `space-3` | 12  | Input inside, badge spacing  |
| `space-4` | 16  | Standard gutter in table     |
| `space-6` | 24  | Card/internal padding        |
| `space-8` | 32  | Page section padding         |
| `space-12`| 48  | Left rail offset, hero top margin |

_Base unit: **4 px**._

## 4. Radii
| Token              | px | Components                     |
|--------------------|----|--------------------------------|
| `radius-none`      | 0  | Table rows, lists              |
| `radius-sm`        | 6  | Badges, small buttons          |
| `radius-md`        | 8  | Inputs, dropdowns              |
| `radius-lg`        | 12 | Cards, side panels             |
| `radius-full`      | 9999 | Avatars, pill tags            |

## 5. Shadows / Elevation
| Token             | CSS value                                   | Usage                    |
|-------------------|---------------------------------------------|--------------------------|
| `shadow-xs`       | `0 1px 2px rgba(0,0,0,.05)`                 | Table header separation  |
| `shadow-sm`       | `0 2px 4px rgba(0,0,0,.06)`                 | Hover rows               |
| `shadow-card`     | `0 4px 12px rgba(0,0,0,.08)`                | Pop-over / side-panel    |
| `shadow-modal`    | `0 8px 24px rgba(0,0,0,.12)`                | Large modal / drawer     |

## 6. Breakpoints   _(Tailwind defaults align well)_
| Name | Min-width |
|------|-----------|
| `sm` | 640px     |
| `md` | 768px     |
| `lg` | 1024px    |
| `xl` | 1280px    |
| `2xl`| 1536px    |

### Container
`max-width: 1360px; margin-inline: auto; padding-inline: 24px;`

## 7. Iconography
- Use **Lucide** or **Heroicons 2.x** outline set.
- Sidebar icons are 20 × 20 px, tint `#FFFFFF` @ 40% opacity; active icon tinted `#FFFFFF`.

## 8. Z-Index Ladder
| Layer            | z-index |
|------------------|---------|
| Global navigation| 50      |
| Side panel/modal | 40      |
| Dropdown / Popover| 30     |
| Table hover row  | 10      |
| Base content     | 0       |

## 9. Motion
| Token             | Value        | Usage                            |
|-------------------|--------------|----------------------------------|
| `ease-standard`   | `cubic-bezier(.4,0,.2,1)` | All default transitions |
| `duration-fast`   | 150 ms       | Hover & tap states               |
| `duration-medium` | 250 ms       | Panel slide-in                   |

---

### How to integrate with Tailwind

```js
// tailwind.config.js (snippet)
const colors = require('tailwindcss/colors')
module.exports = {
  content: ['./app/**/*.{tsx,ts,jsx,js}', './components/**/*.{tsx,ts,jsx,js}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: {
            900: '#0B0130',
            700: '#1C0A53',
            50:  '#F2F1FA',
          },
          highlight1: '#6F56FF',
        },
        state: {
          success: '#64C09B',
          warning: '#F5B547',
          error:   '#F16063',
        },
        surface: {
          0: '#FFFFFF',
          alt: '#F7F7F7',
          border: '#E4E4E4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      borderRadius: {
        sm: '6px',
        md: '8px',
        lg: '12px',
      },
      boxShadow: {
        xs: '0 1px 2px rgba(0,0,0,.05)',
        sm: '0 2px 4px rgba(0,0,0,.06)',
        card: '0 4px 12px rgba(0,0,0,.08)',
        modal: '0 8px 24px rgba(0,0,0,.12)',
      },
    },
  },
}
