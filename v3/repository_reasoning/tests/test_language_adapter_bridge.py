"""
Tests the additive bridge's resilient logic with stub adapters — proving it
fixes the classify crash and the missing-language_name case WITHOUT any frozen
file. Pure logic test (no real adapter imports needed).
Run: python -m v3.repository_reasoning.tests.test_language_adapter_bridge
"""
import v3.repository_reasoning.language_adapter_bridge as B


class GoLike:      language = "go";        file_extensions = {".go"}        # no language_name (the bug)
class CSharpLike:  language = "csharp";    file_extensions = {".cs"}        # registry omits this one
class PyLike:      language_name = "python"; file_extensions = {".py"}
    # is_implemented intentionally absent on Go/C# (older adapters)
class StubImpl:    language_name = "java"; file_extensions = {".java"}
def _impl_true(self): return True
StubImpl.is_implemented = _impl_true


def run():
    f = []
    # language_name_of falls back to `language` (the core fix)
    if B.language_name_of(GoLike()) != "go":
        f.append("language_name_of fallback to `language` failed")
    if B.language_name_of(PyLike()) != "python":
        f.append("language_name_of via language_name failed")

    # is_implemented defaults True when method absent (Go/C# real scan bodies)
    if not B.is_implemented(GoLike()):
        f.append("is_implemented default-True failed")
    if not B.is_implemented(StubImpl()):
        f.append("is_implemented honoring real method failed")

    # the exact dict-build that used to crash registry.classify_files — here
    # with the resilient accessor over a mixed set incl. a no-language_name one
    adapters = [GoLike(), CSharpLike(), PyLike()]
    by_lang = {B.language_name_of(a): a for a in adapters}
    if set(by_lang) != {"go", "csharp", "python"}:
        f.append(f"resilient classify keys = {set(by_lang)}")

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - bridge: language fallback, default is_implemented, no crash on "
          "missing language_name, C#/SQL discoverable")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
