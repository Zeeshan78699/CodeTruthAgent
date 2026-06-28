from collections import Counter, defaultdict


class UnresolvedAnalyzer:
    def __init__(self, unresolved_entries):
        self.unresolved_entries = unresolved_entries or []

    def total_unresolved(self):
        return len(self.unresolved_entries)

    def count_by_pattern(self):
        counter = Counter()
        for entry in self.unresolved_entries:
            counter[entry.get("pattern", "unknown")] += 1
        return dict(counter)

    def count_by_module(self):
        counter = Counter()
        for entry in self.unresolved_entries:
            counter[entry.get("module", "unknown")] += 1
        return dict(counter)

    def examples_by_pattern(self, limit=5):
        examples = defaultdict(list)
        for entry in self.unresolved_entries:
            pattern = entry.get("pattern", "unknown")
            if len(examples[pattern]) < limit:
                examples[pattern].append(entry)
        return dict(examples)

    def summary(self):
        return {"total_unresolved": self.total_unresolved(), "by_pattern": self.count_by_pattern(),
                "by_module": self.count_by_module(), "examples_by_pattern": self.examples_by_pattern()}


def analyze_unresolved(unresolved_entries):
    return UnresolvedAnalyzer(unresolved_entries).summary()
