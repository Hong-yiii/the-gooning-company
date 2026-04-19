# god.md — finance

Assumptions + scenarios — **not** a ledger. Numbers come from **`finance.*`** mocks unless stated otherwise.

## At a glance (demo)

- **Take rate:** **15%** today — **17%** scenario tracked under **`F-001`**.
- **Rough burn:** **~$180k/mo** base (illustrative).
- **Two snapshots:** internal memo (**~11 mo runway** as of **2026-04-01**) vs tool month **`2026-04`** (**~13.4 mo** in `get_financial_report`) — **both are mock**; explain the gap in one line when presenting.

## Projection assumptions (current)

- **Avg order ~$22** · **GMV run-rate ~$220k/mo** (demo fixtures).
- **CAC bands:** buyer **~$8** · baker **~$32** (mocks).
- **Opex flex:** marketing is the main lever in the mock model.

## Last projection snapshot

- **2026-04-01 memo:** cash **~$2.0M** · runway **~11 mo** · breakeven story **~$520k GMV/mo** (illustrative).
- **Tool check:** run **`get_financial_report`** for **`2026-04`** when the room wants a month-shaped table.

## Scenarios tracked

- **17% take rate** — upside vs **baker churn** risk (pairs with **`F-001`**).
- **East Brooklyn push** — pairs with **`P-001`**; watch **one-time CAC** vs **GMV lift** in mocks.
- **Holiday spike** — **`+22% GMV`** Nov–Dec if **`P-002`** ships on time; half that if late.

## Signals from other functions

- **`P-001`** — expect Marketing **opex** asks — **cost** before “runway-neutral” claims.
- **`M-001`** — run **`finance.cost_campaign`** before approving spend story to Maya.

## Open questions for Maya

- Minimum **runway (months)** she wants **before** a formal Series A kickoff?
