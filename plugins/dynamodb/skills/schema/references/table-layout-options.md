# DynamoDB Table Layout Templates

Deep-dive templates for table data visualization with both ASCII and Mermaid Block formats.

## Quick Reference

| Pattern | Use When |
|---------|----------|
| Simple Table | Basic schema visualization |
| Item Collection | Show PK groupings |
| Side-by-Side | Base table + GSI relationship |
| Full Schema | Complete table design |
| Social Network | Multi-entity adjacency list with variable attributes |

## Mermaid Block Configuration

**Tight layout with minimal padding:**
```
%%{init: {"block": {"padding": 8}} }%%
```

**Eliminate gaps between cells** (stroke matches fill):
```
classDef myClass fill:#e1f5fe,stroke:#e1f5fe,stroke-width:7px
```

**Hide block labels** (keeps in code, invisible in render):
```
classDef nolabel color:transparent
class blockName nolabel
```

---

## Templates

### 1. Simple Table

#### ASCII

```
┌──────────────┬─────────────┬──────────────────┬────────────────┬──────────┐
│ PK           │ SK          │ GSI1PK           │ GSI1SK         │ Type     │
├──────────────┼─────────────┼──────────────────┼────────────────┼──────────┤
│ USER#u123    │ PROFILE     │ EMAIL#a@b.com    │ USER#u123      │ User     │
│ USER#u123    │ ORDER#o001  │ STATUS#delivered │ 2024-01-10     │ Order    │
│ USER#u123    │ ORDER#o002  │ STATUS#pending   │ 2024-01-20     │ Order    │
└──────────────┴─────────────┴──────────────────┴────────────────┴──────────┘
```

#### Mermaid Block

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 5

    PK["PK"] SK["SK"] GSI1PK["GSI1PK"] GSI1SK["GSI1SK"] Type["Type"]
    a1["USER#u123"] a2["PROFILE"] a3["EMAIL#a@b"] a4["USER#u123"] a5["User"]
    b1["USER#u123"] b2["ORDER#o001"] b3["STATUS#pending"] b4["2024-01-10"] b5["Order"]
    c1["USER#u123"] c2["ORDER#o002"] c3["STATUS#pending"] c4["2024-01-20"] c5["Order"]

    classDef header fill:#1a1a2e,color:#fff,stroke:#1a1a2e,stroke-width:7px
    classDef user fill:#e1f5fe,stroke:#e1f5fe,stroke-width:7px
    classDef order fill:#fff3e0,stroke:#fff3e0,stroke-width:7px

    class PK,SK,GSI1PK,GSI1SK,Type header
    class a1,a2,a3,a4,a5 user
    class b1,b2,b3,b4,b5,c1,c2,c3,c4,c5 order
```

---

### 2. Item Collection

#### ASCII

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
```

#### Mermaid Block

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 5

    IC1["IC: USER#u123"]:5
    H1["PK"] H2["SK"] H3["GSI1PK"] H4["GSI1SK"] H5["Type"]
    a1["USER#u123"] a2["PROFILE"] a3["EMAIL#a@b"] a4["USER#u123"] a5["User"]
    b1["USER#u123"] b2["ORDER#o001"] b3["STATUS#pending"] b4["2024-01-10"] b5["Order"]
    c1["USER#u123"] c2["ORDER#o002"] c3["STATUS#pending"] c4["2024-01-20"] c5["Order"]

    classDef title fill:#374151,color:#fff,stroke:#374151,stroke-width:7px
    classDef header fill:#1a1a2e,color:#fff,stroke:#1a1a2e,stroke-width:7px
    classDef user fill:#e1f5fe,stroke:#e1f5fe,stroke-width:7px
    classDef order fill:#fff3e0,stroke:#fff3e0,stroke-width:7px

    class IC1 title
    class H1,H2,H3,H4,H5 header
    class a1,a2,a3,a4,a5 user
    class b1,b2,b3,b4,b5,c1,c2,c3,c4,c5 order
```

---

### 3. Side-by-Side (Base + GSI)

#### ASCII

```
Base Table                          GSI1 (overloaded)
┌────────────┬──────────┐           ┌─────────────────┬──────────────┐
│ PK         │ SK       │           │ GSI1PK          │ GSI1SK       │
├────────────┼──────────┤           ├─────────────────┼──────────────┤
│ USER#123   │ PROFILE  │ ───────── │ EMAIL#a@b.com   │ USER#123     │
│ USER#123   │ ORDER#1  │ ───────── │ STATUS#pending  │ 2024-01-15   │
│ PROD#sku-a │ INFO     │ ───────── │ CAT#electronics │ PRICE#299    │
└────────────┴──────────┘           └─────────────────┴──────────────┘
```

#### Mermaid Block

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

    classDef title fill:#374151,color:#fff,stroke:#374151,stroke-width:7px
    classDef header fill:#1a1a2e,color:#fff,stroke:#1a1a2e,stroke-width:7px
    classDef data fill:#f3e8ff,stroke:#f3e8ff,stroke-width:7px

    class BT,GT title
    class BP,BS,GP,GS header
    class b1,b2,b3,b4,b5,b6,g1,g2,g3,g4,g5,g6 data
```

---

### 4. Full Schema

#### ASCII

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
```

#### Mermaid Block

```mermaid
%%{init: {"block": {"padding": 8}} }%%
block-beta
    columns 1

    block:title["ECommerceTable - Single Table Design"]:1
        columns 5
        H1["PK"] H2["SK"] H3["GSI1PK"] H4["GSI1SK"] H5["Type"]

        space:5

        u1["USER#u123"] u2["PROFILE"] u3["EMAIL#a@b.com"] u4["USER#u123"] u5["User"]
        u7["USER#u123"] u8["ORDER#o001"] u9["STATUS#delivered"] u10["2024-01-10"] u11["Order"]
        u13["USER#u123"] u14["ORDER#o002"] u15["STATUS#pending"] u16["2024-01-20"] u17["Order"]

        space:5

        o1["ORDER#o002"] o2["ITEM#sku-a"] o3[" "] o4[" "] o5["LineItem"]

        space:5

        p1["PRODUCT#sku-a"] p2["INFO"] p3["CAT#electronics"] p4["PRICE#299"] p5["Product"]
    end

    classDef header fill:#1a1a2e,color:#fff,stroke:#1a1a2e,stroke-width:7px
    classDef nolabel color:transparent
    classDef user fill:#e3f2fd,stroke:#e3f2fd,stroke-width:7px
    classDef order fill:#fff8e1,stroke:#fff8e1,stroke-width:7px
    classDef lineitem fill:#f3e5f5,stroke:#f3e5f5,stroke-width:7px
    classDef product fill:#e8f5e9,stroke:#e8f5e9,stroke-width:7px

    class H1,H2,H3,H4,H5 header
    class title nolabel
    class u1,u2,u3,u4,u5,u7,u8,u9,u10,u11,u13,u14,u15,u16,u17 user
    class o1,o2,o3,o4,o5 lineitem
    class p1,p2,p3,p4,p5 product
```

---

### 5. Social Network (Adjacency List)

#### Mermaid Block
```mermaid
%%{init: {"block": {"padding": 0}} }%%
block-beta
    columns 6
    
    Primary["Primary Key"]:2 Attributes["Attributes"]:4
    pk["PK"] sk["SK"] attrSpace[" "]:4
    
    u1["u#12345"] c1["'count'"]
    block:countAttrs:4
        columns 4
        fh["follower#"] foh["following#"] ph["post#"] ce1[" "]
        fv["3B"] fov["971"] pv["4945"] ce2[" "]
    end
    
    u2[" "] i1["'info'"]
    block:infoAttrs:4
        columns 4
        nh["name"] ch["content"] ih["imageUrl"] eh["etc"]
        nv["hyuklee"] cv["My name is Hyuk Lee"] iv["s3://..."] ev["..."]
    end
    
    f1["u#12345#follower"] f2["u#23456"] fe1[" "] fe2[" "] fe3[" "] fe4[" "]
    f3[" "] f4["u#34567"] fe5[" "] fe6[" "] fe7[" "] fe8[" "]
    f5[" "] f6["u#45678"] fe9[" "] fe10[" "] fe11[" "] fe12[" "]
    
    g1["u#12345#following"] g2["u#56789"] ge1[" "] ge2[" "] ge3[" "] ge4[" "]
    g3[" "] g4["u#67890"] ge5[" "] ge6[" "] ge7[" "] ge8[" "]
    g5[" "] g6["u#78912"] ge9[" "] ge10[" "] ge11[" "] ge12[" "]
    
    p1["u#12345#post"] p2["p#12345"]
    block:post1Attrs:4
        columns 4
        pch["content"] pih["imageUrl"] pth["timestamp"] pe1[" "]
        pcv["content for a post"] piv["s3://..."] ptv["1571827560"] pe2[" "]
    end
    
    p3[" "] p4["p#23456"]
    block:post2Attrs:4
        columns 4
        pch2["content"] pih2["imageUrl"] pth2["timestamp"] pe3[" "]
        pcv2["content for a post"] piv2["s3://..."] ptv2["1571827561"] pe4[" "]
    end
    
    l1["p#12345#likelist"] l2["u#23456"] le1[" "] le2[" "] le3[" "] le4[" "]
    l3[" "] l4["u#34567"] le5[" "] le6[" "] le7[" "] le8[" "]
    l5[" "] l6["u#45678"] le9[" "] le10[" "] le11[" "] le12[" "]
    
    lc1["p#12345#likecount"] lc2["'count'"]
    block:likecountAttrs:4
        columns 4
        lch["etc"] lce1[" "] lce2[" "] lce3[" "]
        lcv["100"] lce4[" "] lce5[" "] lce6[" "]
    end
    
    t1["u#12345#timeline"] t2["p#34567#u#56789"]
    block:timeline1Attrs:4
        columns 4
        th1["ttl"] te1[" "] te2[" "] te3[" "]
        tv1["1571827560"] te4[" "] te5[" "] te6[" "]
    end
    
    t3[" "] t4["p#45678#u#67890"]
    block:timeline2Attrs:4
        columns 4
        th2["ttl"] te7[" "] te8[" "] te9[" "]
        tv2["1571827560"] te10[" "] te11[" "] te12[" "]
    end
    
    t5[" "] t6["p#56789#u#78901"]
    block:timeline3Attrs:4
        columns 4
        th3["ttl"] te13[" "] te14[" "] te15[" "]
        tv3["1571827560"] te16[" "] te17[" "] te18[" "]
    end

    classDef title fill:#374151,color:#fff,stroke:#374151,stroke-width:7px
    classDef header fill:#1a1a2e,color:#fff,stroke:#1a1a2e,stroke-width:7px
    classDef nolabel fill:transparent,stroke:transparent
    classDef profile fill:#e3f2fd,stroke:#e3f2fd,stroke-width:7px
    classDef follower fill:#e8f5e9,stroke:#e8f5e9,stroke-width:7px
    classDef following fill:#e0f2f1,stroke:#e0f2f1,stroke-width:7px
    classDef post fill:#fff3e0,stroke:#fff3e0,stroke-width:7px
    classDef likelist fill:#f3e5f5,stroke:#f3e5f5,stroke-width:7px
    classDef likecount fill:#fce4ec,stroke:#fce4ec,stroke-width:7px
    classDef timeline fill:#fff8e1,stroke:#fff8e1,stroke-width:7px
    classDef empty fill:transparent,stroke:transparent

    class countAttrs,infoAttrs,post1Attrs,post2Attrs,likecountAttrs,timeline1Attrs,timeline2Attrs,timeline3Attrs nolabel
    class Primary,Attributes title
    class pk,sk header
    class attrSpace title
    class u1,u2,c1,i1 profile
    class fh,foh,ph header
    class fv,fov,pv profile
    class ce1,ce2 empty
    class nh,ch,ih,eh header
    class nv,cv,iv,ev profile
    class f1,f2,f3,f4,f5,f6 follower
    class fe1,fe2,fe3,fe4,fe5,fe6,fe7,fe8,fe9,fe10,fe11,fe12 empty
    class g1,g2,g3,g4,g5,g6 following
    class ge1,ge2,ge3,ge4,ge5,ge6,ge7,ge8,ge9,ge10,ge11,ge12 empty
    class p1,p2,p3,p4 post
    class pch,pih,pth,pch2,pih2,pth2 header
    class pcv,piv,ptv,pcv2,piv2,ptv2 post
    class pe1,pe2,pe3,pe4 empty
    class l1,l2,l3,l4,l5,l6 likelist
    class le1,le2,le3,le4,le5,le6,le7,le8,le9,le10,le11,le12 empty
    class lc1,lc2 likecount
    class lch header
    class lcv likecount
    class lce1,lce2,lce3,lce4,lce5,lce6 empty
    class t1,t2,t3,t4,t5,t6 timeline
    class th1,th2,th3 header
    class tv1,tv2,tv3 timeline
    class te1,te2,te3,te4,te5,te6,te7,te8,te9,te10,te11,te12,te13,te14,te15,te16,te17,te18 empty
```