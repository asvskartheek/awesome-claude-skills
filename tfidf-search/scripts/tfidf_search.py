#!/usr/bin/env python3
"""
TF-IDF Search Engine Implementation

Implements a search engine using TF-IDF vectorization and cosine similarity
to rank documents by relevance to a query.

Usage:
    python tfidf_search.py <csv_file> <text_column> "<query>" [--top_k 10]

Example:
    python tfidf_search.py songs.csv lyrics "love and happiness" --top_k 5
"""

import argparse
import sys

try:
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"Error: Required package not installed: {e.name}", file=sys.stderr)
    print("Install with: uv add numpy pandas scikit-learn", file=sys.stderr)
    print("Or with pip: pip install numpy pandas scikit-learn", file=sys.stderr)
    sys.exit(1)


def load_dataset(csv_path, text_column):
    """Load dataset and validate text column exists."""
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print(f"Error: File is empty: {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if text_column not in df.columns:
        print(f"Error: Column '{text_column}' not found in CSV", file=sys.stderr)
        print(f"Available columns: {', '.join(df.columns)}", file=sys.stderr)
        sys.exit(1)

    # Check for missing values in text column
    null_count = df[text_column].isnull().sum()
    if null_count > 0:
        print(f"Warning: {null_count} rows have missing text, filling with empty string", file=sys.stderr)
        df[text_column] = df[text_column].fillna('')

    return df


def create_tfidf_index(documents):
    """Create TF-IDF vectorizer and transform documents."""
    try:
        vectorizer = TfidfVectorizer(
            max_features=10000,
            min_df=1,
            ngram_range=(1, 2),
            stop_words='english'
        )
        X = vectorizer.fit_transform(documents)
        return vectorizer, X
    except Exception as e:
        print(f"Error creating TF-IDF index: {e}", file=sys.stderr)
        sys.exit(1)


def search(vectorizer, X, query, top_k=10):
    """Search for top-k most similar documents to query."""
    try:
        # Transform query to TF-IDF vector
        query_vec = vectorizer.transform([query])

        # Calculate cosine similarity
        similarities = cosine_similarity(X, query_vec).flatten()

        # Get top-k indices (sorted in descending order)
        top_indices = similarities.argsort()[-top_k:][::-1]

        return top_indices, similarities[top_indices]
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)


def print_results(df, indices, scores, text_column):
    """Print search results in a formatted way."""
    print(f"\n{'='*80}")
    print(f"Top {len(indices)} Results")
    print(f"{'='*80}\n")

    for rank, (idx, score) in enumerate(zip(indices, scores), 1):
        print(f"Rank {rank} | Similarity: {score:.4f}")

        # Print all columns except the text column (show text separately)
        for col in df.columns:
            if col != text_column:
                print(f"  {col}: {df.iloc[idx][col]}")

        # Print text preview (first 200 chars)
        text = str(df.iloc[idx][text_column])
        text_preview = text[:200] + "..." if len(text) > 200 else text
        print(f"  Text Preview: {text_preview}")
        print(f"{'-'*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="TF-IDF based search engine for text datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tfidf_search.py songs.csv lyrics "love and happiness"
  python tfidf_search.py articles.csv content "machine learning" --top_k 5
        """
    )

    parser.add_argument('csv_file', help='Path to CSV file containing the dataset')
    parser.add_argument('text_column', help='Name of the column containing text to search')
    parser.add_argument('query', help='Search query string')
    parser.add_argument('--top_k', type=int, default=10,
                        help='Number of top results to return (default: 10)')

    args = parser.parse_args()

    # Validate inputs
    if args.top_k < 1:
        print("Error: --top_k must be at least 1", file=sys.stderr)
        sys.exit(1)

    if not args.query.strip():
        print("Error: Query cannot be empty", file=sys.stderr)
        sys.exit(1)

    # Load dataset
    print(f"Loading dataset from {args.csv_file}...")
    df = load_dataset(args.csv_file, args.text_column)
    print(f"Loaded {len(df)} documents\n")

    # Create TF-IDF index
    print("Building TF-IDF index...")
    vectorizer, X = create_tfidf_index(df[args.text_column])
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"Feature matrix shape: {X.shape}\n")

    # Search
    print(f"Searching for: '{args.query}'")
    top_k = min(args.top_k, len(df))  # Don't request more results than documents
    indices, scores = search(vectorizer, X, args.query, top_k)

    # Check if any results found
    if scores[0] == 0:
        print("\nNo relevant results found. Query words may not exist in the corpus.")
        print("Try different search terms or check for typos.")
        sys.exit(0)

    # Print results
    print_results(df, indices, scores, args.text_column)


if __name__ == "__main__":
    main()
