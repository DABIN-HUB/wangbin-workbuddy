# Financial Analysis Skills — Market Copy

This copy describes only capabilities currently implemented in the `0.1.3` source. It does not represent WorkBuddy installation, runtime, review, or publication approval.

## Receivables Aging Analysis

For finance and receivables teams, this Skill reads an authorized UTF-8 receivables detail file and reports open balance, overdue balance, aging buckets, and customer-level overdue ranking by an explicit as-of date and currency. Its priority is a customer-level manual-review candidate; it does not provide invoice-by-invoice payment priority or an automated collection plan.

## Inventory Slow-Moving Analysis

For warehouse and operations teams, this Skill reads inventory balance snapshots, receipts, and issues. It reports inventory value and evidence-backed turnover for complete periods, then marks no-movement, slow-moving, overstock, and balance-mismatch candidates. Missing issue data, zero inventory, or incomplete snapshot periods remain explicitly unknown rather than being treated as zero.

## Purchase Price Analysis

For procurement and supply-chain teams, this Skill reads purchase orders containing material, specification, unit, supplier, currency, and tax treatment. It separates same-supplier price movement from cross-supplier quote differences within identical comparable keys and the selected period. A cross-supplier spread is emitted only when the comparison conditions are met; anomalies are observations and investigation leads, not confirmed savings or fraud conclusions.

## Sales Revenue Analysis

For sales and business-analysis teams, this Skill reads authorized sales orders and reports currency-separated revenue, natural-month trend, product revenue ranking, customer contribution, customer concentration, large-order candidates, and data risks. Customer/product acquisition, churn, mix migration, and cross-period structural anomaly detection are not implemented; profit and margin are not inferred.

## Platform boundary

All four candidates are local UTF-8 CSV analysis assets. Their licenses are proprietary and platform distribution terms remain subject to rights-holder confirmation. Local tests and ZIP integrity cannot close `LICENSE_PASS`, WorkBuddy runtime verification, or publication gates.
