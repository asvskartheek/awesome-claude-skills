# TF-IDF Search Examples

This document provides practical examples of using the TF-IDF search skill for various use cases.

## Example 1: Song Lyrics Search

**Dataset**: CSV file with columns: `song`, `artist`, `text` (lyrics)

**Task**: Find songs similar to the query "Take it easy with me, please"

```bash
python .claude/skills/tfidf-search/scripts/tfidf_search.py songdata.csv text "Take it easy with me, please" --top_k 10
```

**Custom Implementation**:
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load song lyrics dataset
df = pd.read_csv('songdata.csv')

# Create TF-IDF vectorizer
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
X = vectorizer.fit_transform(df['text'])

# Search for similar songs
query = "Take it easy with me, please"
query_vec = vectorizer.transform([query])
results = cosine_similarity(X, query_vec).flatten()

# Get top 10 results
top_10 = results.argsort()[-10:][::-1]
for idx in top_10:
    print(f"{df.iloc[idx]['song']} -- {df.iloc[idx]['artist']}")
    print(f"Similarity: {results[idx]:.4f}\n")
```

## Example 2: Article/Document Search

**Dataset**: News articles with columns: `title`, `author`, `content`, `category`

**Task**: Find articles about "machine learning applications in healthcare"

```bash
python .claude/skills/tfidf-search/scripts/tfidf_search.py articles.csv content "machine learning applications in healthcare" --top_k 5
```

**With Custom Preprocessing**:
```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('articles.csv')

# Preprocess: combine title and content for better search
df['combined'] = df['title'] + " " + df['content']

# Create vectorizer with custom parameters
vectorizer = TfidfVectorizer(
    max_features=5000,      # Limit vocabulary
    min_df=2,               # Ignore rare terms
    max_df=0.8,             # Ignore very common terms
    ngram_range=(1, 3),     # Include 1, 2, and 3-word phrases
    stop_words='english'
)

X = vectorizer.fit_transform(df['combined'])

# Search
query = "machine learning applications in healthcare"
query_vec = vectorizer.transform([query])
results = cosine_similarity(X, query_vec).flatten()

# Display results
top_5 = results.argsort()[-5:][::-1]
for idx in top_5:
    print(f"Title: {df.iloc[idx]['title']}")
    print(f"Author: {df.iloc[idx]['author']}")
    print(f"Similarity: {results[idx]:.4f}\n")
```

## Example 3: Product Review Search

**Dataset**: Product reviews with columns: `product_id`, `review_text`, `rating`

**Task**: Find reviews mentioning "battery life problems"

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('reviews.csv')

# Lowercase and clean text
df['review_text'] = df['review_text'].str.lower()

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words='english',
    min_df=2
)

X = vectorizer.fit_transform(df['review_text'])

# Search for battery issues
query = "battery life problems"
query_vec = vectorizer.transform([query])
similarities = cosine_similarity(X, query_vec).flatten()

# Get top matches
top_indices = similarities.argsort()[-20:][::-1]

# Filter by relevance threshold
relevant = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0.1]

for idx, score in relevant:
    print(f"Product ID: {df.iloc[idx]['product_id']}")
    print(f"Rating: {df.iloc[idx]['rating']}")
    print(f"Similarity: {score:.4f}")
    print(f"Review: {df.iloc[idx]['review_text'][:200]}...")
    print("-" * 80)
```

## Example 4: Question-Answer Retrieval

**Dataset**: FAQ database with columns: `question`, `answer`, `category`

**Task**: Find relevant Q&A pairs for user query

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('faq.csv')

# Search on questions only
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words='english'
)

X = vectorizer.fit_transform(df['question'])

def search_faq(user_query, top_k=3):
    """Search FAQ and return top matches with answers."""
    query_vec = vectorizer.transform([user_query])
    similarities = cosine_similarity(X, query_vec).flatten()

    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        if similarities[idx] > 0.05:  # Relevance threshold
            results.append({
                'question': df.iloc[idx]['question'],
                'answer': df.iloc[idx]['answer'],
                'category': df.iloc[idx]['category'],
                'score': similarities[idx]
            })

    return results

# Example usage
user_query = "How do I reset my password?"
matches = search_faq(user_query, top_k=3)

for match in matches:
    print(f"Q: {match['question']}")
    print(f"A: {match['answer']}")
    print(f"Category: {match['category']} | Score: {match['score']:.4f}\n")
```

## Example 5: Semantic Document Clustering

**Task**: Group similar documents together using TF-IDF features

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('documents.csv')

# Create TF-IDF features
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
X = vectorizer.fit_transform(df['text'])

# Cluster documents
n_clusters = 5
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df['cluster'] = kmeans.fit_predict(X)

# For each cluster, find representative documents
for cluster_id in range(n_clusters):
    print(f"\n=== Cluster {cluster_id} ===")
    cluster_docs = df[df['cluster'] == cluster_id]

    # Find documents closest to cluster center
    cluster_center = kmeans.cluster_centers_[cluster_id].reshape(1, -1)
    cluster_X = X[df['cluster'] == cluster_id]

    similarities = cosine_similarity(cluster_X, cluster_center).flatten()
    top_idx = similarities.argsort()[-3:][::-1]

    for idx in top_idx:
        doc_idx = cluster_docs.iloc[idx].name
        print(f"- {df.iloc[doc_idx]['title']}")
```

## Example 6: Multi-field Search

**Task**: Search across multiple text fields (title + description + tags)

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv('products.csv')

# Combine multiple text fields
df['searchable_text'] = (
    df['title'].fillna('') + ' ' +
    df['description'].fillna('') + ' ' +
    df['tags'].fillna('')
)

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words='english',
    max_features=3000
)

X = vectorizer.fit_transform(df['searchable_text'])

# Search
query = "wireless bluetooth headphones noise cancelling"
query_vec = vectorizer.transform([query])
results = cosine_similarity(X, query_vec).flatten()

# Rank and display
top_10 = results.argsort()[-10:][::-1]
for idx in top_10:
    print(f"Product: {df.iloc[idx]['title']}")
    print(f"Score: {results[idx]:.4f}")
    print(f"Price: ${df.iloc[idx]['price']}")
    print("-" * 60)
```

## Advanced: Building a Reusable Search Class

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TFIDFSearchEngine:
    """Reusable TF-IDF search engine class."""

    def __init__(self, vectorizer_params=None):
        """Initialize with optional vectorizer parameters."""
        default_params = {
            'max_features': 5000,
            'ngram_range': (1, 2),
            'stop_words': 'english',
            'min_df': 1
        }

        params = {**default_params, **(vectorizer_params or {})}
        self.vectorizer = TfidfVectorizer(**params)
        self.X = None
        self.df = None

    def fit(self, df, text_column):
        """Fit the search engine on a dataset."""
        self.df = df
        self.X = self.vectorizer.fit_transform(df[text_column])
        return self

    def search(self, query, top_k=10, threshold=0.0):
        """Search and return top-k results above threshold."""
        if self.X is None:
            raise ValueError("Must call fit() before search()")

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(self.X, query_vec).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Filter by threshold
        results = [
            (idx, similarities[idx])
            for idx in top_indices
            if similarities[idx] >= threshold
        ]

        return results

    def get_similar(self, doc_index, top_k=5):
        """Find documents similar to a given document."""
        doc_vec = self.X[doc_index]
        similarities = cosine_similarity(self.X, doc_vec).flatten()

        # Exclude the document itself
        similarities[doc_index] = -1

        top_indices = similarities.argsort()[-top_k:][::-1]
        return [(idx, similarities[idx]) for idx in top_indices]


# Usage example
df = pd.read_csv('articles.csv')

# Create and fit search engine
search_engine = TFIDFSearchEngine(
    vectorizer_params={'ngram_range': (1, 3), 'max_features': 10000}
)
search_engine.fit(df, 'content')

# Search
results = search_engine.search("artificial intelligence in medicine", top_k=5)
for idx, score in results:
    print(f"{df.iloc[idx]['title']} (score: {score:.4f})")

# Find similar articles to article #42
similar = search_engine.get_similar(42, top_k=3)
print(f"\nArticles similar to: {df.iloc[42]['title']}")
for idx, score in similar:
    print(f"- {df.iloc[idx]['title']} (score: {score:.4f})")
```

## Performance Tips

1. **Preprocessing**: Clean text before indexing (lowercase, remove special chars)
2. **Vocabulary Limiting**: Use `max_features` to control memory usage
3. **Stop Words**: Remove common words that don't help distinguish documents
4. **N-grams**: Include bigrams/trigrams for phrase matching
5. **Threshold Filtering**: Only show results above a minimum similarity score
6. **Batch Processing**: For large datasets, process documents in batches

## Common Patterns

### Pattern 1: Interactive Search Loop
```python
while True:
    query = input("Enter search query (or 'quit'): ")
    if query.lower() == 'quit':
        break

    results = search_engine.search(query, top_k=5)
    for idx, score in results:
        print(f"- {df.iloc[idx]['title']} ({score:.4f})")
    print()
```

### Pattern 2: Search with Filters
```python
# Search within a category
category_mask = df['category'] == 'Technology'
category_df = df[category_mask]
category_X = X[category_mask]

query_vec = vectorizer.transform([query])
results = cosine_similarity(category_X, query_vec).flatten()
```

### Pattern 3: Hybrid Search (TF-IDF + Metadata)
```python
# Combine text similarity with metadata scoring
text_scores = cosine_similarity(X, query_vec).flatten()
recency_scores = (df['date'] - df['date'].min()).dt.days / df['date'].max().days

# Weighted combination
combined_scores = 0.7 * text_scores + 0.3 * recency_scores
top_indices = combined_scores.argsort()[-10:][::-1]
```
