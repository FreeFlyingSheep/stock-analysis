# Data API Samples

## Purpose

Store real API responses from CNInfo and Yahoo Finance for:

- Offline development and testing
- Parser validation and schema checks
- Contract compliance verification
- Avoiding unnecessary upstream API calls

## Layout

Provider-specific folders correspond to configuration files:

- `cninfo/`: Responses from CNInfo API endpoints
- `yahoo/`: Responses from Yahoo Finance endpoints

Each JSON file:

- Named to match the endpoint in `configs/api/`
- Contains the complete raw API response
- Preserves structure to validate schema conformance

## Filename Conventions

Config files use snake_case endpoint names:

- Config: `configs/api/cninfo/get_balance_sheets.yaml`
- Data: `data/api/cninfo/balance_sheets.json`

## Response Structure

Each API response JSON file follows its endpoint's contract as defined in `configs/api/`:

```json
{
  "path": "/financialData/getBalanceSheets",
  "code": 200,
  "data": {
    "total": <count>,
    "count": <count>,
    "resultMsg": "success",
    "result": [...]
  }
}
```

Responses include:

- `path`: The API endpoint path
- `code`: HTTP status code (typically 200)
- `data`: The actual response payload (varies by endpoint)

## Adding or Refreshing Sample Data

When you need to update a sample response:

1. **Get fresh data from the real endpoint**:
   - Use the adaptor directly: `python -c "..."`
   - Or call the endpoint manually with proper parameters

2. **Save the full JSON response**:
   - Pretty-print the response for readability
   - Save to `data/api/<provider>/<endpoint>.json`
   - Ensure structure matches config specification

3. **Clean sensitive data** (if needed):
   - Strip company names, contact info, or confidential data
   - Preserve structural shapes for schema validation
   - Keep representative values (e.g., keep some balance sheet numbers)

4. **Validate against schema**:
   - Ensure response matches the contract in `configs/api/<provider>/<endpoint>.yaml`
   - Check that top-level `path` and `code` fields are present
   - Verify nested structure matches configuration

5. **Keep configs and data in sync**:
   - When upstream contract changes, update both:
     - `configs/api/<provider>/<endpoint>.yaml` (schema definition)
     - `data/api/<provider>/<endpoint>.json` (sample data)

## Current Endpoints

### CNInfo API

Balance sheet, cash flow, income statement, and company metadata:

- `balance_sheets.json` - Assets, liabilities, equity
- `cash_flow_statement.json` - Cash inflows and outflows
- `income_statement.json` - Revenue, costs, profits
- `company_introduction.json` - Company profile and details
- `company_executives.json` - Management team information
- `main_indicators.json` - Key financial metrics

Equity and ownership data:

- `stock_structure.json` - Shareholder structure
- `top_ten_stockholders.json` - Major shareholders
- `top_ten_circulating_stockholders.json` - Shareholders with free-trading shares
- `stockholder_num.json` - Shareholder count breakdown
- `equity_pledge.json` - Pledged equity information

Corporate events and activities:

- `company_his_dividend.json` - Dividend history
- `lift_ban.json` - Share lift-off restrictions
- `executives_inc_dec_detail.json` - Executive share trading
- `stockholeder_inc_dec_detail.json` - Shareholder share trading
- `margin_trading.json` - Margin trading activity
- `ints_detail.json` - Interest payment details
- `fund_holdings.json` - Fund holdings of the stock

### Yahoo Finance API

Historical stock price data:

- `history.json` - Daily OHLCV data for a stock

## Best Practices

- **Don't hand-edit responses**: Regenerate from real API calls to prevent drift
- **Keep structures complete**: If truncating large arrays, keep at least one full example of each data shape
- **Document major changes**: Add comments when sample data is updated with new fields or structure changes
- **Version control**: Track changes so you can compare old vs. new contracts when debugging issues

## Using Sample Data in Tests

The sample JSON files can be used in unit tests:

```python
import json

with open('data/api/cninfo/balance_sheets.json') as f:
    sample_response = json.load(f)

# Test parser against known response structure
result = parser.parse_balance_sheets(sample_response)
assert result.total == sample_response['data']['total']
```

This ensures tests don't depend on live API availability and run consistently.
