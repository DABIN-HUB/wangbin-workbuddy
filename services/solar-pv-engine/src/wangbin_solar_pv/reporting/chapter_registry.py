"""Load and verify the complete frozen chapter specification."""
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files

from ..errors import ContractError
from .compat import CHAPTERS, APPENDICES, APPENDIX_TITLES
from ..serialization import loads


class Registry:
    def __init__(self, catalog):
        root = files(__package__).joinpath("specs")
        text = root.joinpath("report-spec.json").read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        lock = loads(root.joinpath("spec-lock.json").read_bytes())
        self.hash = sha256(text.encode("utf-8")).hexdigest()
        if self.hash != lock["sha256"]:
            raise ContractError("REPORT_SPEC_DRIFT")
        self.spec = loads(text)
        if self.spec["report_spec_version"] != lock["version"]:
            raise ContractError("REPORT_SPEC_VERSION")
        if [(c["chapter_id"], c["chapter_title"], tuple(s["section_title"] for s in c["sections"]))
                for c in self.spec["chapters"]] != list(CHAPTERS):
            raise ContractError("REPORT_SPEC_OUTLINE")
        if [(a["appendix_id"], a["title"]) for a in self.spec["appendices"]] != list(APPENDICES):
            raise ContractError("REPORT_SPEC_APPENDICES")
        if {s["section_id"]: s["title"] for a in self.spec["appendices"] for s in a["sections"]} != APPENDIX_TITLES:
            raise ContractError("REPORT_SPEC_APPENDIX_ITEMS")
        if self.spec["baseline_hashes"] != catalog.baseline_hashes:
            raise ContractError("REPORT_SPEC_BASELINE")
        for ch in self.spec["chapters"]:
            for sec in ch["sections"]:
                if set(sec["input_fields"]) - catalog.fields.keys() or set(sec["formula_ids"]) - catalog.formulas.keys():
                    raise ContractError("REPORT_SPEC_REFERENCE")
        self._chapters = {c["chapter_id"]: c for c in self.spec["chapters"]}

    def chapter(self, chapter_id):
        if chapter_id not in self._chapters:
            raise ContractError("UNKNOWN_CHAPTER")
        return deepcopy(self._chapters[chapter_id])
