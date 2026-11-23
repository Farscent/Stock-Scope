# StockScope dashboard design

Mode: Operate. Standard Streamlit sidebar, tabs, metrics, charts and sortable tables.
Product decisions come from the user's detailed brief (PRODUCT.md).

Grounded visual directions considered, ordered by relevance: shareholder report,
economics journal, exchange fact sheet, corporate annual review, business atlas,
investment research digest, statistical yearbook. The local design helper selected
the sixth direction (`seed:9cf8ffc92bb26d53`); remote challengers were unavailable.
The user authorized routine decisions without a further selection round.

The investment research digest contributes a warm paper ground, dark ink,
deep green Tesla and burnt orange GameStop series, clear type hierarchy and
compact tabular numerals. Its signature is an observed-date caption directly
above market KPIs and period-end labeling beneath revenue bars. Layout and
controls remain native dashboard conventions, with no decorative report imitation.

First view: filters on the left, market overview on the right; company revenue,
comparison, exports and methodology are always one tab away. Missing-data states
retain the navigation and explain how to retry. A single selected session cannot
produce a return. Revenue keeps its independent reporting horizon.

No decorative imagery or motion is needed. Charts supply the visual evidence.
The main risk is limited source availability, addressed by explicit unavailable
states and actual observation dates rather than simulated content.
