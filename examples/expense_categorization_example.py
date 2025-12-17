#!/usr/bin/env python3
"""
Example: Expense Categorization and Analysis

This example demonstrates AI-powered expense categorization
and spending analysis.
"""

from src.expense_categorization import ExpenseCategorizer
import pandas as pd
import json


def main():
    # Initialize categorizer
    categorizer = ExpenseCategorizer()
    
    # Sample expense data
    expenses = [
        {"description": "Office supplies from Staples", "vendor": "Staples", "amount": 245.50, "date": "2024-01-15"},
        {"description": "Microsoft 365 subscription", "vendor": "Microsoft", "amount": 150.00, "date": "2024-01-15"},
        {"description": "Electric bill - January", "vendor": "Con Edison", "amount": 320.00, "date": "2024-01-20"},
        {"description": "Client lunch meeting", "vendor": "The Capital Grille", "amount": 185.75, "date": "2024-01-22"},
        {"description": "Laptop for new employee", "vendor": "Dell", "amount": 1299.00, "date": "2024-01-25"},
        {"description": "Legal consultation", "vendor": "Smith Legal LLP", "amount": 500.00, "date": "2024-01-28"},
        {"description": "Internet service", "vendor": "Verizon", "amount": 89.99, "date": "2024-01-30"},
        {"description": "QuickBooks subscription", "vendor": "Intuit", "amount": 80.00, "date": "2024-02-01"},
        {"description": "Flight to client site", "vendor": "American Airlines", "amount": 450.00, "date": "2024-02-05"},
        {"description": "Hotel for business trip", "vendor": "Marriott", "amount": 285.00, "date": "2024-02-06"},
    ]
    
    print("=" * 80)
    print("EXPENSE CATEGORIZATION EXAMPLE")
    print("=" * 80)
    
    # Categorize expenses
    print("\n1. Categorizing expenses...")
    categorized_expenses = categorizer.categorize_batch(expenses)
    
    # Display categorized expenses
    print("\n2. Categorized Expenses:")
    print("-" * 80)
    for i, expense in enumerate(categorized_expenses, 1):
        print(f"\n   {i}. {expense['description']}")
        print(f"      Vendor: {expense.get('vendor', 'N/A')}")
        print(f"      Amount: ${expense['amount']:,.2f}")
        print(f"      Category: {expense['category']}")
        print(f"      GL Account: {categorizer.suggest_gl_account(expense['category'])}")
        print(f"      Confidence: {expense['confidence']:.2%}")
        if expense['needs_review']:
            print(f"      ⚠️  Needs manual review (low confidence)")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(categorized_expenses)
    
    # Spending analysis
    print("\n3. Spending Analysis:")
    print("-" * 80)
    analysis = categorizer.analyze_spending_patterns(df)
    
    print(f"\n   Total Expenses: ${analysis['total_expenses']:,.2f}")
    
    print("\n   By Category:")
    for category, stats in analysis['by_category'].items():
        print(f"      {category}:")
        print(f"         Total: ${stats['sum']:,.2f}")
        print(f"         Average: ${stats['mean']:,.2f}")
        print(f"         Count: {stats['count']}")
    
    # Tax deductible summary
    print("\n4. Tax Deductible Summary:")
    print("-" * 80)
    tax_summary = categorizer.get_tax_deductible_summary(df)
    
    print(f"\n   Fully Deductible: ${tax_summary['fully_deductible']:,.2f}")
    print(f"   Partially Deductible: ${tax_summary['partially_deductible']:,.2f}")
    print(f"   Not Deductible: ${tax_summary['not_deductible']:,.2f}")
    print(f"\n   Total Deductible: ${tax_summary['total_deductible']:,.2f}")
    
    print("\n   Details by Category:")
    for category, details in tax_summary['details'].items():
        print(f"      {category}: ${details['amount']:,.2f} "
              f"({details['deductible_rate']:.0%} deductible)")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
