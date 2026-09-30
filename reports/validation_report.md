# Validation Report

- Raw rows: 11816
- Clean rows: 11200
- Duplicate ticket IDs: 616
- Status: warning

## Checks
- duplicate_ticket_ids: pass
  - {"duplicate_ticket_ids": 616, "duplicated_rows": 1232}
- invalid_timestamps: pass
  - {"invalid_created_at": 0, "invalid_first_response_at": 0}
- first_response_before_created: pass
  - {"count": 0}
- resolution_timestamp_validation: warning
  - {"missing_resolved_at": 589}
- missing_critical_fields: warning
  - {"columns_with_missing_values": ["order_id"]}
- unexpected_status_values: pass
- unexpected_channel_values: pass
- invalid_priority_values: pass
- impossible_csat_values: warning
  - {"count": 1730}
- suspicious_negative_refund_values: pass
  - {"count": 0}
