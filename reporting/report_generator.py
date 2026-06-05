"""
CodeTruth Agent V2
Report Generator
"""

from typing import Dict, Any
import json


class ReportGenerator:

    @staticmethod
    def generate_console_report(data: Dict[str, Any]):

        print("\nGenerated Report")
        print("-" * 60)

        print(json.dumps(data, indent=4))

        print("-" * 60)