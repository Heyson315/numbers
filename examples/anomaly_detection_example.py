#!/usr/bin/env python3
"""
Example: Audit and Anomaly Detection

This example demonstrates fraud detection and anomaly detection
capabilities for financial data.
"""

from src.anomaly_detection import AnomalyDetector, FraudRiskScorer
import pandas as pd
from datetime import datetime, timedelta
import json


def main():
    # Initialize detectors
    anomaly_detector = AnomalyDetector(contamination=0.1)
    fraud_scorer = FraudRiskScorer()
    
    # Sample transaction data with intentional anomalies
    transactions = []
    base_date = datetime(2024, 1, 1)
    
    # Normal transactions
    for i in range(20):
        transactions.append({
            'amount': 100 + (i * 5),
            'vendor': f'Vendor {i % 5}',
            'date': (base_date + timedelta(days=i)).isoformat(),
            'description': f'Regular payment {i}'
        })
    
    # Add anomalies
    # 1. Unusually large transaction
    transactions.append({
        'amount': 15000.00,
        'vendor': 'Suspicious Vendor',
        'date': (base_date + timedelta(days=21)).isoformat(),
        'description': 'Large unusual payment'
    })
    
    # 2. Duplicate transaction
    transactions.append({
        'amount': 150.00,
        'vendor': 'Vendor 2',
        'date': (base_date + timedelta(days=5, hours=1)).isoformat(),
        'description': 'Possible duplicate'
    })
    
    # 3. Round number transactions (potential fraud indicator)
    transactions.append({
        'amount': 10000.00,
        'vendor': 'Vendor 3',
        'date': (base_date + timedelta(days=22)).isoformat(),
        'description': 'Round number payment'
    })
    
    # 4. Weekend transaction
    transactions.append({
        'amount': 500.00,
        'vendor': 'Vendor 4',
        'date': (base_date + timedelta(days=23)).isoformat(),  # Sunday
        'description': 'Weekend transaction'
    })
    
    df = pd.DataFrame(transactions)
    
    print("=" * 80)
    print("AUDIT AND ANOMALY DETECTION EXAMPLE")
    print("=" * 80)
    
    # Detect anomalies
    print("\n1. Detecting transaction anomalies...")
    results = anomaly_detector.detect_transaction_anomalies(df)
    anomalies = results[results['is_anomaly']]
    
    print(f"\n   Total transactions: {len(df)}")
    print(f"   Anomalies detected: {len(anomalies)}")
    print(f"   Anomaly rate: {len(anomalies) / len(df) * 100:.1f}%")
    
    if len(anomalies) > 0:
        print("\n   Anomalous transactions:")
        for idx, row in anomalies.iterrows():
            print(f"\n      Transaction #{idx}")
            print(f"         Amount: ${row['amount']:,.2f}")
            print(f"         Vendor: {row['vendor']}")
            print(f"         Date: {row['date']}")
            print(f"         Anomaly Score: {row['anomaly_score']:.3f}")
    
    # Detect duplicates
    print("\n2. Detecting duplicate transactions...")
    duplicates = anomaly_detector.detect_duplicate_transactions(df)
    
    if duplicates:
        print(f"\n   Found {len(duplicates)} potential duplicate(s):")
        for dup in duplicates:
            print(f"\n      Match:")
            print(f"         Transaction 1: ${dup['transaction_1']['amount']:,.2f} on {dup['transaction_1']['date']}")
            print(f"         Transaction 2: ${dup['transaction_2']['amount']:,.2f} on {dup['transaction_2']['date']}")
            print(f"         Time difference: {dup['time_difference_hours']:.1f} hours")
            print(f"         Confidence: {dup['confidence']:.1%}")
    else:
        print("   No duplicates detected")
    
    # Round number analysis
    print("\n3. Analyzing round number patterns...")
    round_analysis = anomaly_detector.detect_round_number_fraud(df)
    round_count = round_analysis['is_round_number'].sum()
    
    print(f"\n   Round number transactions: {round_count}")
    print(f"   Round number rate: {round_count / len(df) * 100:.1f}%")
    
    if round_count > 0:
        round_txs = round_analysis[round_analysis['is_round_number']]
        print("\n   Round number transactions found:")
        for idx, row in round_txs.iterrows():
            print(f"      ${row['amount']:,.2f} - {row['vendor']}")
    
    # Benford's Law analysis
    print("\n4. Benford's Law Analysis...")
    benford_result = anomaly_detector.detect_benford_law_violations(
        df['amount'].tolist()
    )
    
    if 'error' not in benford_result:
        print(f"\n   Chi-square statistic: {benford_result['chi_square']:.2f}")
        print(f"   Critical value (α=0.05): {benford_result['critical_value']:.2f}")
        print(f"   Follows Benford's Law: {'✓ Yes' if benford_result['follows_benford'] else '✗ No'}")
        
        if not benford_result['follows_benford']:
            print("\n   ⚠️  WARNING: Data does not follow Benford's Law!")
            print("      This may indicate potential fraud or data manipulation.")
    
    # Timing anomalies
    print("\n5. Detecting timing anomalies...")
    timing_anomalies = anomaly_detector.detect_unusual_timing_patterns(df)
    
    if timing_anomalies:
        for anomaly in timing_anomalies:
            print(f"\n   {anomaly['type']}:")
            print(f"      Count: {anomaly['count']}")
            print(f"      Total amount: ${anomaly['total_amount']:,.2f}")
    else:
        print("   No timing anomalies detected")
    
    # Fraud risk scoring
    print("\n6. Fraud Risk Scoring...")
    high_risk_transactions = []
    
    for idx, row in df.iterrows():
        transaction = row.to_dict()
        risk_assessment = fraud_scorer.calculate_transaction_risk(transaction)
        
        if risk_assessment['requires_review']:
            high_risk_transactions.append({
                'transaction': transaction,
                'risk': risk_assessment
            })
    
    if high_risk_transactions:
        print(f"\n   Found {len(high_risk_transactions)} high-risk transaction(s):")
        for item in high_risk_transactions:
            tx = item['transaction']
            risk = item['risk']
            print(f"\n      Transaction: ${tx['amount']:,.2f} - {tx['vendor']}")
            print(f"      Risk Level: {risk['risk_level'].upper()}")
            print(f"      Risk Score: {risk['risk_score']:.2f}")
            print(f"      Risk Factors:")
            for factor in risk['risk_factors']:
                print(f"         - {factor['details']}")
    
    # Generate comprehensive report
    print("\n7. Generating comprehensive audit report...")
    audit_report = anomaly_detector.generate_audit_report(df)
    
    print("\n   Report Summary:")
    print(f"      Report Date: {audit_report['report_date']}")
    print(f"      Total Transactions: {audit_report['total_transactions']}")
    
    print("\n" + "=" * 80)
    print("Audit analysis complete!")
    print("=" * 80)
    
    # Save detailed report
    with open('/tmp/audit_report.json', 'w') as f:
        json.dump(audit_report, f, indent=2, default=str)
    
    print("\nDetailed report saved to: /tmp/audit_report.json")


if __name__ == "__main__":
    main()
