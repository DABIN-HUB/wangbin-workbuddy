"""Named compatibility seam for retained non-narrative report utilities.

Phase G may remove fixed prose, NOT these frozen structure/model/style helpers.
No call to build_claim or an old narrative generator belongs in this module.
"""
from ..report_export import (ReportModel, CHAPTERS, APPENDICES, _metric_label as metric_label,
                             _decision_metric_text as metric_text, _metric_unit as metric_unit,
                             _irr_presentation as irr_presentation, _add_table as add_table)
from ..report_claims import APPENDIX_TITLES, _source_value as source_value
