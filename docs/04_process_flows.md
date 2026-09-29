# 04. Process Flows

Diagrams are written in Mermaid and render directly on GitHub.

## 1. Customer journey (current state)

The journey from browsing to a possible second purchase, with the data captured at each step
and the point where the dataset lets us observe drop-off.

```mermaid
flowchart LR
    A[Browse and select product] --> B[Place order]
    B --> C{Payment approved?}
    C -- No --> X1[Order canceled]
    C -- Yes --> D[Seller prepares order]
    D --> E[Handed to carrier]
    E --> F[In transit]
    F --> G{Delivered by estimated date?}
    G -- Yes --> H[Delivered on time]
    G -- No --> I[Delivered late]
    H --> J[Review request sent]
    I --> J
    J --> K{Review left?}
    K -- Yes --> L[Review score 1 to 5]
    K -- No --> M[No feedback captured]
    L --> N{Second order placed?}
    M --> N
    N -- Yes --> O[Repeat customer]
    N -- No --> P[One-time customer]

    style P fill:#fdd,stroke:#c33
    style I fill:#fed,stroke:#c73
    style O fill:#dfd,stroke:#3a3
```

### Where each step is measured

| Step | Source column (`dw.fact_orders`) |
|---|---|
| Place order | `purchase_ts`, `order_status` |
| Payment approved | `approved_ts` |
| Handed to carrier | `carrier_ts` |
| Delivered | `delivered_ts`, `delivery_days` |
| On time or late | `is_late`, `delay_days` |
| Review | `review_score` |
| Second order | `customer_order_seq`, `cohort_month` |

## 2. Funnel stages analysed in Phase 2

```mermaid
flowchart TD
    S1[Orders placed] --> S2[Approved]
    S2 --> S3[Shipped to carrier]
    S3 --> S4[Delivered]
    S4 --> S5[Reviewed]
    S5 --> S6[Second order]
```

The funnel query counts orders reaching each stage and the conversion between stages.
The largest expected drop is the last step, which is the subject of this project.

## 3. Proposed future state: proactive delay handling

Supports US-05 (delay notification) and US-08 (review follow-up).

```mermaid
flowchart TD
    A[Order handed to carrier] --> B[Carrier scan received]
    B --> C{Predicted to miss estimate?}
    C -- No --> D[No action]
    C -- Yes --> E[Send delay notification with new date]
    E --> F[Order delivered]
    D --> F
    F --> G[Review request]
    G --> H{Score 2 or below?}
    H -- Yes --> I[Create support ticket]
    I --> J[Resolve and inform customer]
    H -- No --> K{First order?}
    J --> K
    K -- Yes --> L[Send second-order offer after set delay]
    K -- No --> M[Standard communication]
```

## 4. Requirements process followed in this project

```mermaid
flowchart LR
    A[Problem framing] --> B[Stakeholder map]
    B --> C[BRD and KPIs]
    C --> D[User stories]
    D --> E[Data model and quality checks]
    E --> F[Analysis]
    F --> G[Recommendations]
    G --> H[RICE roadmap]
    H --> I[PRD and A/B test plan]
```

## Notes and limitations

- The future-state flow is a proposal. No part of it is validated until the A/B test is run.
- The dataset has no browse or cart events, so the journey is observable only from order placement onward.
- Delay prediction (the decision in the future-state flow) is out of scope for the analysis; the flow
  shows where such a capability would sit.
