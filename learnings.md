Observed behaviour: model adds extra comparison numbers if after being prompted not to. 
Hypothesis: It copies the full retrieved sentence 
Small Fix: Constraint single-value answers to the value + period + source
(I noticed that even when the answer was grounded, the model sometimes copied extra nearby facts from the retrieved chunk. So I added answer-shape constraints and tested whether single-metric questions returned only the requested metric. This helped distinguish factual grounding from answer discipline.)


RED FLAG: Company-specific risks or negative signals in the latest 10-Q that could affect revenue, margins, liquidity, legal exposure, operations, or investor interpretation.
