# Causal feature and inference contract

Record: `{id, timestamp, sender, receiver, amount, currency:'CAD', label?:0|1}`. Timestamps use chronological UTC ISO `YYYY-MM-DDTHH:mm:ssZ` or three fractional digits. Python groups parsed equivalent instants; JS accepts canonical UTC strings only and rejects impossible dates, unsorted rows and duplicate IDs. Amount must be positive, finite, have at most two decimal places and be at most CAD 1 billion. Account strings are lookup keys; they are not numerical model inputs. Synthetic labels and IDs are not consumed in feature generation or scoring.

Histories store and aggregate exact integer cents, then divide totals by 100 for numerical features. This avoids cancellation when large historical amounts expire and a small remainder stays. Browser input is capped at 20,000 rows: at CAD 1 billion per row the largest total is 2e15 cents, below JavaScript's exact-integer limit 2^53. Sub-cent amounts are rejected rather than silently rounded. The 10,001-row extreme-expiry regression leaves one cent after thousands of large transfers expire.

For event time `t`, the history window is **[t − 86,400 seconds, t)**. The lower boundary is included and the current instant is excluded. Same-instant events are all scored against the prior history, then the whole group is appended. No first-in-group event can inform another event at the same instant. `so`: sender's prior outgoing events, `si`: sender's prior incoming events, `ri`: receiver's prior incoming events. Totals sum CAD amounts. Empty counts/totals/unique recipient counts are zero. `log` below is natural `log1p`.

| Index | Name | Formula |
|---:|---|---|
| 0 | log_amount | log(amount) |
| 1 | log_sender_out_count_24h | log(count(so)) |
| 2 | log_sender_out_total_24h | log(total(so)) |
| 3 | log_receiver_in_count_24h | log(count(ri)) |
| 4 | log_receiver_in_total_24h | log(total(ri)) |
| 5 | log_sender_in_count_24h | log(count(si)) |
| 6 | log_sender_in_total_24h | log(total(si)) |
| 7 | log_sender_unique_receivers_24h | log(number of distinct so receivers) |
| 8 | amount_to_sender_mean_24h | min(20, amount / (mean(so) + 1)); empty mean = 0 |
| 9 | sender_in_to_out_ratio_24h | min(20, total(si) / (total(so) + amount + 1)) |
| 10 | log_seconds_since_sender_in | log(min(86400, t − most recent si time)); empty = log(86400) |

LR exported mean/scale are fitted on training data only. `z = intercept + sum(((feature_i−mean_i)/scale_i) * coefficient_i)`, score = sigmoid(z). Contributions omit the intercept and report signed additive standardized log-odds terms. RF exports each tree's left/right child, feature index, split threshold and positive-class leaf probability. Cast inputs to float32, descend using `<= threshold` to left, average leaf probabilities over all 32 trees. Both JS implementations are directly executable and verified against Python reference outputs.

IDs/account names have no effect when consistently renamed. Earlier scores are invariant to appending later rows. Changes to a row can change its own and later scores; a what-if edit must rerun the chronological sequence. Derived features do not explicitly detect cycles or graph embeddings; the displayed transaction network is a visualization, not an independently trained graph neural network.
