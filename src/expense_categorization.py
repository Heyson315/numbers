"""
AI-Powered Expense Categorization Module

Automatically categorizes expenses using machine learning
and provides intelligent suggestions for accounting workflows.
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder


class ExpenseCategorizer:
    """AI-powered expense categorization system."""

    def __init__(self):
        """Initialize expense categorizer."""
        self.categories = {
            'office_supplies': ['paper', 'pens', 'pencils', 'folders', 'stapler', 'desk'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'cellular'],
            'rent': ['rent', 'lease', 'office space', 'building'],
            'payroll': ['salary', 'wages', 'payroll', 'compensation', 'benefits'],
            'insurance': ['insurance', 'coverage', 'premium', 'policy'],
            'professional_services': ['consulting', 'legal', 'accounting', 'advisory', 'audit'],
            'marketing': ['advertising', 'marketing', 'promotion', 'social media', 'seo'],
            'travel': ['hotel', 'flight', 'airfare', 'transportation', 'lodging', 'uber', 'lyft'],
            'meals': ['restaurant', 'food', 'lunch', 'dinner', 'catering', 'meal'],
            'software': ['software', 'subscription', 'saas', 'license', 'cloud'],
            'hardware': ['computer', 'laptop', 'monitor', 'printer', 'server'],
            'training': ['training', 'education', 'course', 'certification', 'workshop'],
            'maintenance': ['repair', 'maintenance', 'service', 'cleaning'],
            'miscellaneous': ['other', 'miscellaneous', 'general']
        }

        self.vectorizer = None
        self.model = None
        self.label_encoder = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the ML model with training data."""
        # Create training data from category keywords
        training_data = []
        training_labels = []

        for category, keywords in self.categories.items():
            for keyword in keywords:
                # Create variations
                training_data.append(keyword)
                training_labels.append(category)
                training_data.append(f"{keyword} expense")
                training_labels.append(category)
                training_data.append(f"payment for {keyword}")
                training_labels.append(category)

        # Initialize vectorizer and model
        self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        feature_matrix = self.vectorizer.fit_transform(training_data)

        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(training_labels)

        self.model = MultinomialNB()
        self.model.fit(feature_matrix, encoded_labels)

    def categorize(
        self,
        description: str,
        vendor: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        Categorize an expense.

        Args:
            description: Expense description
            vendor: Vendor name (optional)
            amount: Expense amount (optional)

        Returns:
            Tuple of (category, confidence_score)
        """
        # Combine description and vendor for better accuracy
        text = description.lower()
        if vendor:
            text = f"{text} {vendor.lower()}"

        # Use ML model to predict category
        feature_matrix = self.vectorizer.transform([text])
        prediction = self.model.predict(feature_matrix)[0]
        probabilities = self.model.predict_proba(feature_matrix)[0]

        category = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(max(probabilities))

        # Apply business rules for high-value transactions
        if amount and amount > 10000:
            if any(word in text for word in ['rent', 'lease', 'property']):
                return 'rent', 0.95
            elif any(word in text for word in ['payroll', 'salary', 'wages']):
                return 'payroll', 0.95

        return category, confidence

    def categorize_batch(
        self,
        expenses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Categorize a batch of expenses.

        Args:
            expenses: List of expense dictionaries

        Returns:
            List of expenses with added category and confidence
        """
        results = []

        for expense in expenses:
            category, confidence = self.categorize(
                description=expense.get('description', ''),
                vendor=expense.get('vendor'),
                amount=expense.get('amount')
            )

            expense_copy = expense.copy()
            expense_copy['category'] = category
            expense_copy['confidence'] = confidence
            expense_copy['needs_review'] = confidence < 0.7

            results.append(expense_copy)

        return results

    def suggest_gl_account(self, category: str) -> str:
        """
        Suggest general ledger account based on category.

        Args:
            category: Expense category

        Returns:
            Suggested GL account code
        """
        gl_mapping = {
            'office_supplies': '6100',
            'utilities': '6200',
            'rent': '6300',
            'payroll': '7000',
            'insurance': '6400',
            'professional_services': '6500',
            'marketing': '6600',
            'travel': '6700',
            'meals': '6710',
            'software': '6800',
            'hardware': '6810',
            'training': '6900',
            'maintenance': '6950',
            'miscellaneous': '6999'
        }

        return gl_mapping.get(category, '6999')

    def analyze_spending_patterns(
        self,
        expenses_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze spending patterns from expense data.

        Args:
            expenses_df: DataFrame with expense data

        Returns:
            Analysis results
        """
        if 'category' not in expenses_df.columns:
            return {'error': 'Category column not found'}

        analysis = {
            'total_expenses': float(expenses_df['amount'].sum()),
            'by_category': {},
            'top_vendors': {},
            'monthly_trend': {},
            'unusual_transactions': []
        }

        # Spending by category
        category_spending = expenses_df.groupby('category')['amount'].agg(['sum', 'mean', 'count'])
        analysis['by_category'] = category_spending.to_dict('index')

        # Top vendors
        if 'vendor' in expenses_df.columns:
            top_vendors = expenses_df.groupby('vendor')['amount'].sum().sort_values(ascending=False).head(10)
            analysis['top_vendors'] = top_vendors.to_dict()

        # Detect unusual transactions (using Z-score)
        if len(expenses_df) > 10:
            mean_amount = expenses_df['amount'].mean()
            std_amount = expenses_df['amount'].std()

            if std_amount > 0:
                expenses_df['z_score'] = (expenses_df['amount'] - mean_amount) / std_amount
                unusual = expenses_df[abs(expenses_df['z_score']) > 2.5]

                analysis['unusual_transactions'] = unusual[[
                    'description', 'amount', 'category'
                ]].to_dict('records')

        return analysis

    def get_tax_deductible_summary(
        self,
        expenses_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate tax deductible expense summary.

        Args:
            expenses_df: DataFrame with expense data

        Returns:
            Tax summary
        """
        # Define tax-deductible categories
        fully_deductible = [
            'office_supplies', 'utilities', 'rent', 'insurance',
            'professional_services', 'software', 'hardware',
            'training', 'maintenance'
        ]

        partially_deductible = {
            'meals': 0.5,  # 50% deductible
            'travel': 1.0,  # Fully deductible if business-related
        }

        summary = {
            'fully_deductible': 0.0,
            'partially_deductible': 0.0,
            'not_deductible': 0.0,
            'details': {}
        }

        if 'category' not in expenses_df.columns:
            return summary

        for category in expenses_df['category'].unique():
            category_expenses = expenses_df[expenses_df['category'] == category]['amount'].sum()

            if category in fully_deductible:
                summary['fully_deductible'] += category_expenses
                summary['details'][category] = {
                    'amount': float(category_expenses),
                    'deductible_rate': 1.0
                }
            elif category in partially_deductible:
                rate = partially_deductible[category]
                summary['partially_deductible'] += category_expenses * rate
                summary['details'][category] = {
                    'amount': float(category_expenses),
                    'deductible_rate': rate
                }
            else:
                summary['not_deductible'] += category_expenses
                summary['details'][category] = {
                    'amount': float(category_expenses),
                    'deductible_rate': 0.0
                }

        summary['total_deductible'] = (
            summary['fully_deductible'] + summary['partially_deductible']
        )

        return summary


class SmartReconciliation:
    """AI-powered transaction reconciliation system."""

    def __init__(self):
        """Initialize reconciliation system."""
        self.match_threshold = 0.85

    def fuzzy_match_transactions(
        self,
        bank_transactions: List[Dict[str, Any]],
        book_transactions: List[Dict[str, Any]],
        amount_tolerance: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Match bank transactions with book transactions using optimized hash-based approach.

        Args:
            bank_transactions: List of bank transactions
            book_transactions: List of book transactions
            amount_tolerance: Allowed difference in amounts

        Returns:
            List of matched transaction pairs

        Performance: O(n+m) average case using amount-based bucketing,
        much faster than O(n*m) naive approach for large datasets.
        """
        matches = []

        # Build amount-based index for book transactions
        # This allows us to quickly find candidates with similar amounts
        book_amount_index = {}
        for idx, book_tx in enumerate(book_transactions):
            amount = abs(float(book_tx.get('amount', 0)))
            # Round to create buckets (handles tolerance)
            bucket = round(amount * 100)  # Cent precision
            if bucket not in book_amount_index:
                book_amount_index[bucket] = []
            book_amount_index[bucket].append((idx, book_tx))

        matched_book_indices = set()
        unmatched_bank = []

        for bank_tx in bank_transactions:
            bank_amount = abs(float(bank_tx.get('amount', 0)))
            bank_bucket = round(bank_amount * 100)

            best_match = None
            best_match_idx = None
            best_score = 0

            # Check current bucket and adjacent buckets for tolerance
            # Enforce a minimum bucket size to avoid missing matches for small transactions
            min_tolerance_buckets = 1  # Minimum number of buckets to check on each side
            calculated_tolerance_buckets = int(bank_amount * amount_tolerance * 100) + 1
            tolerance_buckets = max(min_tolerance_buckets, calculated_tolerance_buckets)
            for bucket_offset in range(-tolerance_buckets, tolerance_buckets + 1):
                check_bucket = bank_bucket + bucket_offset

                if check_bucket not in book_amount_index:
                    continue

                # Only check candidates in relevant buckets
                for book_idx, book_tx in book_amount_index[check_bucket]:
                    if book_idx in matched_book_indices:
                        continue

                    score = self._calculate_match_score(
                        bank_tx, book_tx, amount_tolerance
                    )

                    if score > best_score and score >= self.match_threshold:
                        best_score = score
                        best_match = book_tx
                        best_match_idx = book_idx

            if best_match:
                matches.append({
                    'bank_transaction': bank_tx,
                    'book_transaction': best_match,
                    'match_score': best_score,
                    'status': 'matched'
                })
                matched_book_indices.add(best_match_idx)
            else:
                unmatched_bank.append(bank_tx)

        # Add unmatched transactions
        for bank_transaction in unmatched_bank:
            matches.append({
                'bank_transaction': bank_transaction,
                'book_transaction': None,
                'match_score': 0,
                'status': 'unmatched_bank'
            })
        # Find unmatched book transactions
        for idx, book_tx in enumerate(book_transactions):
            if idx not in matched_book_indices:
                matches.append({
                    'bank_transaction': None,
                    'book_transaction': book_tx,
                    'match_score': 0,
                    'status': 'unmatched_book'
                })

        return matches

    def _calculate_match_score(
        self,
        bank_tx: Dict[str, Any],
        book_tx: Dict[str, Any],
        amount_tolerance: float
    ) -> float:
        """Calculate similarity score between two transactions."""
        score = 0.0

        # Amount match (most important)
        bank_amount = abs(float(bank_tx.get('amount', 0)))
        book_amount = abs(float(book_tx.get('amount', 0)))

        if bank_amount > 0:
            amount_diff = abs(bank_amount - book_amount) / bank_amount
            if amount_diff <= amount_tolerance:
                score += 0.6
            elif amount_diff <= 0.05:
                score += 0.4

        # Date proximity
        bank_date = bank_tx.get('date')
        book_date = book_tx.get('date')

        if bank_date and book_date:
            from datetime import datetime
            if isinstance(bank_date, str):
                bank_date = datetime.fromisoformat(bank_date)
            if isinstance(book_date, str):
                book_date = datetime.fromisoformat(book_date)

            days_diff = abs((bank_date - book_date).days)
            if days_diff == 0:
                score += 0.3
            elif days_diff <= 2:
                score += 0.2
            elif days_diff <= 5:
                score += 0.1

        # Description similarity
        bank_desc = str(bank_tx.get('description', '')).lower()
        book_desc = str(book_tx.get('description', '')).lower()

        if bank_desc and book_desc:
            common_words = set(bank_desc.split()) & set(book_desc.split())
            if common_words:
                score += 0.1

        return score
