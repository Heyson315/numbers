# Performance Best Practices for Developers

## Quick Reference Guide

This guide helps developers avoid common performance pitfalls when contributing to the codebase.

## ❌ Don't Do This

### 1. Nested Loops with Large Datasets
```python
# BAD: O(n²) complexity
for item1 in large_list1:
    for item2 in large_list2:
        if match(item1, item2):
            results.append((item1, item2))
```

### 2. DataFrame iterrows()
```python
# BAD: Very slow iteration
for index, row in df.iterrows():
    process_row(row)
```

### 3. Repeated Pattern Compilation
```python
# BAD: Compiles pattern every call
def extract_data(text):
    matches = re.findall(r'\d+', text)
    return matches
```

### 4. String Concatenation in Loops
```python
# BAD: Creates new string each iteration
result = ""
for item in items:
    result += str(item) + "\n"
```

### 5. Copying Large DataFrames Unnecessarily
```python
# BAD: Multiple unnecessary copies
df1 = df.copy()
df2 = df1.copy()
df3 = df2.copy()
```

## ✅ Do This Instead

### 1. Use Hash-Based Lookups
```python
# GOOD: O(n+m) complexity with indexing
index = {key(item): item for item in large_list2}
for item1 in large_list1:
    if key(item1) in index:
        results.append((item1, index[key(item1)]))
```

### 2. Use Vectorized Operations or itertuples()
```python
# GOOD: Vectorized pandas operation
df['new_column'] = df['old_column'].apply(process_value)

# GOOD: Or use itertuples() if needed
for row in df.itertuples():
    process_row(row)
```

### 3. Pre-compile Patterns
```python
# GOOD: Compile once, use many times
class DataExtractor:
    def __init__(self):
        self.pattern = re.compile(r'\d+')
    
    def extract_data(self, text):
        return self.pattern.findall(text)
```

### 4. Use List Join
```python
# GOOD: Efficient string building
parts = [str(item) for item in items]
result = "\n".join(parts)
```

### 5. Copy Only When Necessary
```python
# GOOD: Single copy when needed
if need_to_modify:
    df_modified = df.copy()
    df_modified['new_col'] = values
    return df_modified
else:
    return df  # No copy needed
```

## Common Patterns to Use

### Pattern 1: Groupby for Efficient Aggregation
```python
# Group data first, then process groups
grouped = df.groupby('category')
for name, group in grouped:
    process_group(group)  # Each group is smaller
```

### Pattern 2: Early Exit
```python
# Exit as soon as condition met
for item in items:
    if found_what_we_need(item):
        return result  # Don't keep searching
```

### Pattern 3: Use Sets for Membership Testing
```python
# O(1) lookup instead of O(n)
valid_ids = set(id_list)
if item_id in valid_ids:  # Fast lookup
    process(item)
```

### Pattern 4: Batch Processing
```python
# Process in chunks for large datasets
chunk_size = 1000
for i in range(0, len(data), chunk_size):
    chunk = data[i:i+chunk_size]
    process_chunk(chunk)
```

### Pattern 5: Cache Expensive Computations
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(input_data):
    # This result will be cached
    return compute_result(input_data)
```

## Complexity Cheat Sheet

| Operation | Bad | Good |
|-----------|-----|------|
| Find item | O(n) list | O(1) dict/set |
| Match pairs | O(n²) nested loops | O(n) hash join |
| String building | O(n²) += in loop | O(n) list join |
| DataFrame iteration | O(n) iterrows() | O(n) vectorized |
| Pattern matching | O(n) compile each time | O(1) pre-compile |

## Performance Testing

### Always Add Performance Tests
```python
def test_performance():
    import time
    data = generate_large_dataset(1000)
    
    start = time.time()
    result = your_function(data)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"Too slow: {elapsed}s"
```

### Profile Before Optimizing
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
your_function()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)  # Top 10 slowest
```

## When to Optimize

1. ✅ **Profile first** - Don't guess, measure
2. ✅ **Optimize hot paths** - Focus on frequently executed code
3. ✅ **Fix algorithmic issues** - O(n²) → O(n) has biggest impact
4. ❌ **Don't over-optimize** - Readability matters
5. ❌ **Don't optimize prematurely** - Get it working first

## Red Flags in Code Review

Watch for these patterns:
- [ ] Nested loops over large datasets
- [ ] `.iterrows()` on DataFrames
- [ ] Repeated regex pattern compilation
- [ ] String concatenation in loops
- [ ] Multiple DataFrame copies
- [ ] No early exit conditions
- [ ] Linear search when hash lookup possible

## Measuring Performance

### Add Timing Logs
```python
import logging
import time

logger = logging.getLogger(__name__)

def process_data(data):
    start = time.time()
    result = expensive_operation(data)
    elapsed = time.time() - start
    
    logger.info(f"Processed {len(data)} items in {elapsed:.2f}s")
    return result
```

### Use Context Managers
```python
from contextlib import contextmanager
import time

@contextmanager
def timed(name):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"{name}: {elapsed:.3f}s")

# Usage
with timed("Data processing"):
    process_large_dataset()
```

## Resources

- See `docs/PERFORMANCE_OPTIMIZATIONS.md` for detailed case studies
- Run `pytest tests/test_performance.py` for performance benchmarks
- Use `python -m cProfile` for profiling
- Check pandas documentation for vectorized operations

## Questions?

If you're unsure whether your code might have performance issues:
1. Run the performance tests: `pytest tests/test_performance.py`
2. Profile your code with sample large datasets
3. Ask in code review if the complexity seems high
4. Refer to this guide and the optimization docs
