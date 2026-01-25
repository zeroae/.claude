# DynamoDB Table Layout Diagram Options

Comparison of ASCII vs Mermaid Block for visualizing DynamoDB table structure.

## Quick Comparison

| Format | Pros | Cons | Best For |
|--------|------|------|----------|
| **ASCII** | Universal, precise control, no rendering deps | No color, manual alignment | Terminal, any environment |
| **Mermaid Block** | Color coding, rendered visual | Newer syntax, verbose | Documentation, presentations |

## Mermaid Block Configuration

Add this directive at the start for tight layout with minimal internal padding:

```
%%{init: {"block": {"padding": 8}} }%%
```

To hide block labels while keeping them in code:

```
classDef nolabel color:transparent
class blockName nolabel
```

---

## 1. Simple Table

### ASCII

```
┌──────────────┬─────────────┬──────────────────┬────────────────┬──────────┐
│ PK           │ SK          │ GSI1PK           │ GSI1SK         │ Type     │
├──────────────┼─────────────┼──────────────────┼────────────────┼──────────┤
│ USER#u123    │ PROFILE     │ EMAIL#a@b.com    │ USER#u123      │ User     │
│ USER#u123    │ ORDER#o001  │ STATUS#delivered │ 2024-01-10     │ Order    │
│ USER#u123    │ ORDER#o002  │ STATUS#pending   │ 2024-01-20     │ Order    │
│ ORDER#o002   │ ITEM#sku-a  │ -                │ -              │ LineItem │
│ PRODUCT#sku-a│ INFO        │ CAT#electronics  │ PRICE#299      │ Product  │
└──────────────┴─────────────┴──────────────────┴────────────────┴──────────┘
```

### Mermaid Block (Color-Coded)

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 5

    PK["PK"] SK["SK"] GSI1PK["GSI1PK"] GSI1SK["GSI1SK"] Type["Type"]

    a1["USER#u123"] a2["PROFILE"] a3["EMAIL#a@b"] a4["USER#u123"] a5["User"]
    b1["USER#u123"] b2["ORDER#o001"] b3["STATUS#pending"] b4["2024-01-10"] b5["Order"]
    c1["USER#u123"] c2["ORDER#o002"] c3["STATUS#pending"] c4["2024-01-20"] c5["Order"]
    d1["ORDER#o002"] d2["ITEM#sku-a"] d3[" "] d4[" "] d5["LineItem"]
    e1["PRODUCT#sku-a"] e2["INFO"] e3["CAT#electronics"] e4["PRICE#299"] e5["Product"]

    classDef header fill:#1a1a2e,color:#fff
    classDef user fill:#e1f5fe,stroke:#0288d1
    classDef order fill:#fff3e0,stroke:#f57c00
    classDef lineitem fill:#f3e5f5,stroke:#7b1fa2
    classDef product fill:#e8f5e9,stroke:#388e3c

    class PK,SK,GSI1PK,GSI1SK,Type header
    class a1,a2,a3,a4,a5 user
    class b1,b2,b3,b4,b5,c1,c2,c3,c4,c5 order
    class d1,d2,d3,d4,d5 lineitem
    class e1,e2,e3,e4,e5 product
```

---

## 2. Item Collection Grouping

### ASCII

```
┌─ Item Collection: USER#u123 ────────────────────────────────────────────────┐
│                                                                             │
│  PK          │ SK              │ GSI1PK           │ GSI1SK      │ Type      │
│  ────────────┼─────────────────┼──────────────────┼─────────────┼────────── │
│  USER#u123   │ PROFILE         │ EMAIL#a@b.com    │ USER#u123   │ User      │
│  USER#u123   │ ORDER#o001      │ STATUS#delivered │ 2024-01-10  │ Order     │
│  USER#u123   │ ORDER#o002      │ STATUS#pending   │ 2024-01-20  │ Order     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Item Collection: ORDER#o002 ───────────────────────────────────────────────┐
│                                                                             │
│  PK          │ SK              │ GSI1PK           │ GSI1SK      │ Type      │
│  ────────────┼─────────────────┼──────────────────┼─────────────┼────────── │
│  ORDER#o002  │ ITEM#sku-a      │ -                │ -           │ LineItem  │
│  ORDER#o002  │ ITEM#sku-b      │ -                │ -           │ LineItem  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Item Collection: PRODUCT#sku-a ────────────────────────────────────────────┐
│                                                                             │
│  PK            │ SK          │ GSI1PK          │ GSI1SK     │ Type         │
│  ──────────────┼─────────────┼─────────────────┼────────────┼───────────── │
│  PRODUCT#sku-a │ INFO        │ CAT#electronics │ PRICE#299  │ Product      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Block (Color-Coded)

> **Note:** Spanning title rows cause wider horizontal spacing than Simple Table.

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 5

    IC1["IC: USER#u123"]:5
    H1["PK"] H2["SK"] H3["GSI1PK"] H4["GSI1SK"] H5["Type"]
    a1["USER#u123"] a2["PROFILE"] a3["EMAIL#a@b"] a4["USER#u123"] a5["User"]
    b1["USER#u123"] b2["ORDER#o001"] b3["STATUS#pending"] b4["2024-01-10"] b5["Order"]
    c1["USER#u123"] c2["ORDER#o002"] c3["STATUS#pending"] c4["2024-01-20"] c5["Order"]

    space:5

    IC2["IC: ORDER#o002"]:5
    H6["PK"] H7["SK"] H8["GSI1PK"] H9["GSI1SK"] H10["Type"]
    d1["ORDER#o002"] d2["ITEM#sku-a"] d3[" "] d4[" "] d5["LineItem"]
    e1["ORDER#o002"] e2["ITEM#sku-b"] e3[" "] e4[" "] e5["LineItem"]

    space:5

    IC3["IC: PRODUCT#sku-a"]:5
    H11["PK"] H12["SK"] H13["GSI1PK"] H14["GSI1SK"] H15["Type"]
    f1["PRODUCT#sku-a"] f2["INFO"] f3["CAT#electronics"] f4["PRICE#299"] f5["Product"]

    classDef title fill:#374151,color:#fff
    classDef header fill:#1a1a2e,color:#fff
    classDef user fill:#e1f5fe,stroke:#0288d1
    classDef order fill:#fff3e0,stroke:#f57c00
    classDef lineitem fill:#f3e5f5,stroke:#7b1fa2
    classDef product fill:#e8f5e9,stroke:#388e3c

    class IC1,IC2,IC3 title
    class H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,H11,H12,H13,H14,H15 header
    class a1,a2,a3,a4,a5 user
    class b1,b2,b3,b4,b5,c1,c2,c3,c4,c5 order
    class d1,d2,d3,d4,d5,e1,e2,e3,e4,e5 lineitem
    class f1,f2,f3,f4,f5 product
```

---

## 3. Base Table + GSI

### ASCII (Recommended for Side-by-Side)

```
Base Table                          GSI1 (overloaded)
┌────────────┬──────────┐           ┌─────────────────┬──────────────┐
│ PK         │ SK       │           │ GSI1PK          │ GSI1SK       │
├────────────┼──────────┤           ├─────────────────┼──────────────┤
│ USER#123   │ PROFILE  │ ───────── │ EMAIL#a@b.com   │ USER#123     │
│ USER#123   │ ORDER#1  │ ───────── │ STATUS#pending  │ 2024-01-15   │
│ PROD#sku-a │ INFO     │ ───────── │ CAT#electronics │ PRICE#299    │
└────────────┴──────────┘           └─────────────────┴──────────────┘

GSI1 serves multiple access patterns:
• Find user by email:    GSI1PK = EMAIL#...
• Find pending orders:   GSI1PK = STATUS#pending
• Products by category:  GSI1PK = CAT#electronics
```

### Mermaid Block (Side-by-Side with Links)

Uses a 5-column layout with space separators and arrow links showing the projection relationship:

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 5

    BT["Base Table"]:2 space:1 GT["GSI1 (Overloaded)"]:2
    BP["PK"] BS["SK"] space GP["GSI1PK"] GS["GSI1SK"]
    b1["USER#123"] b2["PROFILE"] space g1["EMAIL#a@b.com"] g2["USER#123"]
    b3["USER#123"] b4["ORDER#1"] space g3["STATUS#pending"] g4["2024-01-15"]
    b5["PROD#sku-a"] b6["INFO"] space g5["CAT#electronics"] g6["PRICE#299"]

    b2 --> g1
    b4 --> g3
    b6 --> g5

    classDef title fill:#374151,color:#fff
    classDef header fill:#1a1a2e,color:#fff

    class BT,GT title
    class BP,BS,GP,GS header
```

---

## 4. Full Schema (E-Commerce)

### ASCII

```
┌─ Base Table: ECommerceTable ────────────────────────────────────────────────┐
│                                                                             │
│  PK            │ SK              │ GSI1PK           │ GSI1SK      │ Type    │
│  ──────────────┼─────────────────┼──────────────────┼─────────────┼──────── │
│  USER#u123     │ PROFILE         │ EMAIL#a@b.com    │ USER#u123   │ User    │
│  USER#u123     │ ORDER#o001      │ STATUS#delivered │ 2024-01-10  │ Order   │
│  USER#u123     │ ORDER#o002      │ STATUS#pending   │ 2024-01-20  │ Order   │
│  ORDER#o002    │ ITEM#sku-a      │ -                │ -           │ LineItem│
│  PRODUCT#sku-a │ INFO            │ CAT#electronics  │ PRICE#299   │ Product │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ GSI1: Overloaded Index ────────────────────────────────────────────────────┐
│                                                                             │
│  GSI1PK           │ GSI1SK      │ Base PK        │ Base SK      │ Purpose   │
│  ─────────────────┼─────────────┼────────────────┼──────────────┼────────── │
│  EMAIL#a@b.com    │ USER#u123   │ USER#u123      │ PROFILE      │ By email  │
│  STATUS#delivered │ 2024-01-10  │ USER#u123      │ ORDER#o001   │ By status │
│  STATUS#pending   │ 2024-01-20  │ USER#u123      │ ORDER#o002   │ By status │
│  CAT#electronics  │ PRICE#299   │ PRODUCT#sku-a  │ INFO         │ By cat    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Block (Color-Coded)

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 1

    block:title["ECommerceTable - Single Table Design"]:1
        columns 6
        H1["PK"] H2["SK"] H3["GSI1PK"] H4["GSI1SK"] H5["Type"] H6["Attrs"]

        space:6

        u1["USER#u123"] u2["PROFILE"] u3["EMAIL#a@b.com"] u4["USER#u123"] u5["User"] u6["name,email"]
        u7["USER#u123"] u8["ADDR#home"] u9[" "] u10[" "] u11["Address"] u12["street,city"]
        u13["USER#u123"] u14["ORDER#o001"] u15["STATUS#delivered"] u16["2024-01-10"] u17["Order"] u18["total"]
        u19["USER#u123"] u20["ORDER#o002"] u21["STATUS#pending"] u22["2024-01-20"] u23["Order"] u24["total"]

        space:6

        o1["ORDER#o001"] o2["META"] o3[" "] o4[" "] o5["OrderMeta"] o6["address"]
        o7["ORDER#o001"] o8["ITEM#sku-a"] o9[" "] o10[" "] o11["LineItem"] o12["qty,price"]
        o13["ORDER#o001"] o14["ITEM#sku-b"] o15[" "] o16[" "] o17["LineItem"] o18["qty,price"]

        space:6

        p1["PRODUCT#sku-a"] p2["INFO"] p3["CAT#electronics"] p4["PRICE#299"] p5["Product"] p6["name,desc"]
        p7["PRODUCT#sku-a"] p8["REVIEW#r001"] p9["RATING#5"] p10["2024-01-15"] p11["Review"] p12["text"]
    end

    classDef header fill:#1a1a2e,color:#fff
    classDef nolabel color:transparent
    classDef user fill:#e3f2fd,stroke:#1976d2
    classDef order fill:#fff8e1,stroke:#ffa000
    classDef product fill:#e8f5e9,stroke:#43a047

    class H1,H2,H3,H4,H5,H6 header
    class title nolabel
    class u1,u2,u3,u4,u5,u6,u7,u8,u9,u10,u11,u12,u13,u14,u15,u16,u17,u18,u19,u20,u21,u22,u23,u24 user
    class o1,o2,o3,o4,o5,o6,o7,o8,o9,o10,o11,o12,o13,o14,o15,o16,o17,o18 order
    class p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12 product
```

---

## Recommendations

| Scenario | ASCII | Mermaid Block |
|----------|-------|---------------|
| Quick schema sketch | Simple | Simple |
| Show item collections | Grouped | Nested |
| Explain GSI overloading | Side-by-Side | Side-by-Side with Links |
| Color-coded entities | - | Color-Coded |
| Full schema overview | Full Schema | Full Schema (Color) |
| Terminal output | Any | - |
| Documentation | - | Any |
