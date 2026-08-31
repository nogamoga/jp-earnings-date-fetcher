# jp-earnings-date-fetcher

JPX「決算発表予定日」の月次xlsxを、株価と `merge_asof` しやすい JSON にします。

## 使い方

```bash
pip install -e .
python -m jpx_earnings fetch --out docs/v1
python examples/merge_prices.py --prices prices.csv --events docs/v1/events.json
```
