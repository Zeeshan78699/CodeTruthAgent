from typing import Any, Dict, List

from .unresolved_analyzer import UnresolvedAnalyzer
from .cause_classifier import CauseClassifier
from .fact_extractor_v2 import extract_facts_v2 as extract_facts
from .builtin_type_engine import run_builtin_type_engine
from .constructor_tracking_engine import run_constructor_tracking_engine
from .factory_return_engine import run_factory_return_engine
from .property_type_engine import run_property_type_engine
from .property_type_table_builder import build_property_type_table
from .inheritance_resolver import InheritanceResolver
from .reflection_resolver import ReflectionResolver
from .flatten_class_graph import flatten_class_graph, flatten_return_type_table, build_bare_name_index
from .assignment_chain_builder import build_assignment_table
from .factory_origin_tracker import FACTORY_PREFIXES
from .variable_origin_extractor import VariableOriginExtractor


def _looks_like_factory_name(function_name, bare_name_index):
    if not function_name or function_name in bare_name_index:
        return False
    return any(function_name.startswith(p) for p in FACTORY_PREFIXES)


def _resolve_bare_name(bare_name, bare_name_index):
    """
    FIX (main-pipeline integration): flat_class_graph is now keyed by
    fully-qualified name, not bare name (see flatten_class_graph.py) -
    a deliberate fix for the silent same-name-collision risk that was
    fine for a one-repo exploratory script but not for code that runs
    across many repos. A bare name at a call site (e.g. "Flask" in
    "app = Flask(...)") has no module-qualification info available
    without resolving that module's own import aliases - real work not
    yet built here. So this only resolves a bare name when it maps to
    EXACTLY ONE qualified class repo-wide; if it's ambiguous (two
    classes share that name in different modules) or matches nothing,
    it stays unresolved rather than silently guessing the wrong one.
    """
    matches = bare_name_index.get(bare_name)
    if not matches or len(matches) != 1:
        return None
    return matches[0]


def _enrich_origin_facts(extracted_facts, assignment_table, flat_class_graph,
                          bare_name_index, origin_extractor):
    """
    FIX: fact_extractor (v1/v2) only ever extracted attribute_name from
    the note text - the note never contained the variable name the
    attribute was called on, so constructor_class/factory_function had
    no way to ever get populated, independent of the class_graph shape
    fix. This re-derives the variable name via VariableOriginExtractor,
    then chains it through the real assignment table to find what (if
    anything) proved-constructed or proved-factoried it.
    """
    enriched = []
    for fact in extracted_facts:
        fact = dict(fact)
        if fact.get("pattern") == "attribute_call" and fact.get("attribute_name"):
            module = fact.get("module")
            lineno = fact.get("lineno")
            variable_name = origin_extractor.extract_variable_name(
                module, lineno, fact["attribute_name"]
            )
            if variable_name:
                origin = assignment_table.get(f"{module}:{variable_name}")
                if origin and origin.get("origin_type") == "call":
                    candidate = origin.get("origin_name")
                    qualified = _resolve_bare_name(candidate, bare_name_index)
                    if qualified:
                        fact["constructor_class"] = qualified
                    elif _looks_like_factory_name(candidate, bare_name_index):
                        fact["factory_function"] = candidate
        enriched.append(fact)
    return enriched


class ResolutionPipeline:

    def __init__(self, unresolved_entries, return_type_table, class_graph,
                 repo_path=None, function_graph=None, module_graph=None,
                 rename_fn=None):
        self.unresolved_entries = unresolved_entries or []
        self.class_graph = class_graph or {}
        self.repo_path = repo_path

        # FIX: flatten both shape-mismatched inputs ONCE, here, before any
        # resolver sees them. function_graph is required to build methods
        # per class - see flatten_class_graph.py for why.
        self.function_graph = function_graph or {}
        self.flat_class_graph = flatten_class_graph(self.class_graph, self.function_graph)
        self.flat_return_type_table = flatten_return_type_table(return_type_table or {})
        # FIX (main-pipeline integration): bare-name collision fix -
        # see flatten_class_graph.py / build_bare_name_index.
        self.bare_name_index = build_bare_name_index(self.flat_class_graph)

        # FIX: build the assignment table + origin extractor needed to
        # populate constructor_class/factory_function for real - see
        # _enrich_origin_facts and variable_origin_extractor.py.
        # rename_fn (FIX, main-pipeline integration): when the caller's
        # report had the src-layout rename applied (subtree_naming.py),
        # this builder's own independent file scan must apply the SAME
        # rename or its keys silently stop matching the rest of the
        # report - see assignment_chain_builder.py.
        self.module_graph = module_graph or {}
        self.assignment_table = build_assignment_table(repo_path, rename_fn=rename_fn) if repo_path else {}
        self.origin_extractor = VariableOriginExtractor(repo_path, self.module_graph) if repo_path else None

    def run(self) -> Dict[str, Any]:
        baseline_count = len(self.unresolved_entries)

        analyzer = UnresolvedAnalyzer(self.unresolved_entries)
        analysis_report = analyzer.summary()

        classifier = CauseClassifier()
        classification_report = classifier.classify_all(self.unresolved_entries)
        classified_entries = []
        for entry in self.unresolved_entries:
            cause = classifier.classify_entry(entry)
            enriched = dict(entry)
            enriched["cause"] = cause
            classified_entries.append(enriched)

        extracted_facts = extract_facts(classified_entries)

        # FIX: populate constructor_class/factory_function for real -
        # previously always None, see _enrich_origin_facts above.
        if self.origin_extractor is not None:
            extracted_facts = _enrich_origin_facts(
                extracted_facts, self.assignment_table,
                self.flat_class_graph, self.bare_name_index, self.origin_extractor,
            )

        builtin_results = run_builtin_type_engine(extracted_facts)
        remaining = builtin_results["remaining_entries"]

        # FIX: use the flattened class graph, not the raw module-keyed one.
        constructor_results = run_constructor_tracking_engine(remaining, self.flat_class_graph)
        remaining = constructor_results["remaining_entries"]

        # FIX: use the flattened return-type table AND the flattened class graph.
        factory_results = run_factory_return_engine(
            remaining, self.flat_return_type_table, self.flat_class_graph, self.bare_name_index
        )
        remaining = factory_results["remaining_entries"]

        if self.repo_path:
            property_type_table = build_property_type_table(self.repo_path, self.flat_class_graph, self.bare_name_index)
        else:
            property_type_table = {}

        property_results = run_property_type_engine(remaining, property_type_table, self.flat_class_graph)
        remaining = property_results["remaining_entries"]

        # FIX: use the flattened class graph + bare_name_index for base-class fallback.
        inheritance_resolver = InheritanceResolver(self.flat_class_graph, self.bare_name_index)
        inheritance_results = inheritance_resolver.resolve_batch(remaining)
        remaining = inheritance_results["remaining_entries"]

        reflection_resolver = ReflectionResolver(self.flat_class_graph)
        reflection_results = reflection_resolver.resolve_batch(remaining)
        remaining = reflection_results["remaining_entries"]

        final_unresolved = len(remaining)
        total_resolved = (
            builtin_results["resolved_count"] + constructor_results["resolved_count"]
            + factory_results["resolved_count"] + property_results["resolved_count"]
            + inheritance_results["resolved_count"] + reflection_results["resolved_count"]
        )
        reduction_pct = round((total_resolved / baseline_count) * 100, 2) if baseline_count > 0 else 0.0

        return {
            "baseline_unresolved": baseline_count,
            "analysis": analysis_report,
            "classification": classification_report,
            "facts_extracted": len(extracted_facts),
            "resolver_results": {
                "builtin_type": builtin_results["resolved_count"],
                "constructor": constructor_results["resolved_count"],
                "factory": factory_results["resolved_count"],
                "property": property_results["resolved_count"],
                "inheritance": inheritance_results["resolved_count"],
                "reflection": reflection_results["resolved_count"],
            },
            "final": {
                "resolved_by_pipeline": total_resolved,
                "remaining_unresolved": final_unresolved,
                "reduction_pct": reduction_pct,
            },
            "remaining_unresolved_entries": remaining,
        }


def run_resolution_pipeline(unresolved_entries, return_type_table, class_graph,
                             repo_path=None, function_graph=None, module_graph=None,
                             rename_fn=None):
    pipeline = ResolutionPipeline(
        unresolved_entries=unresolved_entries,
        return_type_table=return_type_table,
        class_graph=class_graph,
        repo_path=repo_path,
        function_graph=function_graph,
        module_graph=module_graph,
        rename_fn=rename_fn,
    )
    return pipeline.run()
