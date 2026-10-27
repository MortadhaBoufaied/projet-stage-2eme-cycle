class AnalysisAssistant:
 def summarize_payment(self,result):
  total=len(result);counts=result.final_status.value_counts().to_dict();return {'headline':f'{total:,} customers assessed','summary':f"{counts.get('MANUAL_REVIEW',0):,} require manual review, {counts.get('REVIEW_RECOMMENDED',0):,} need review, and {counts.get('STANDARD_PROCESS',0):,} can follow the standard process.",'actions':['Review manual-review records first.','Verify source data before consequential action.','Export the report for the accountable reviewer.']}
 def summarize_forecast(self,result):
  anomalies=int(result.get('is_anomaly',[]).sum());stock=int(result.get('is_stockout_risk',[]).sum());return {'headline':f'{len(result):,} forecast observations analyzed','summary':f'{anomalies:,} anomalies and {stock:,} stockout-risk observations were detected.','actions':['Review stockout exposures.','Investigate large forecast deviations.','Use forecasts as decision support, not automatic orders.']}
