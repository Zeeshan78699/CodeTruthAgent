"""
CodeTruth Agent V2
Memory Store V2
"""

import json
import os
import uuid
import shutil

from json import JSONDecodeError
from datetime import datetime
from typing import Dict, Any


class MemoryStoreV2:

    def __init__(self, memory_file="memory_v2.json"):

        self.memory_file = memory_file
        self.backup_directory = "backups"
        self.archive_directory = "backups/memory_archives"

        self.max_approved_decisions = 100
        self.max_recovery_events = 50
        self.max_cleanup_events = 50
        
        self.max_archive_cleanup_events = 50
        self.max_archive_files = 25

        os.makedirs(self.backup_directory, exist_ok=True)
        os.makedirs(self.archive_directory, exist_ok=True)

        if not os.path.exists(self.memory_file):
            self._initialize_memory()

    def _default_memory(self) -> Dict[str, Any]:

        return {
            "approved_decisions": [],
            "rejected_decisions": [],
            "safe_patterns": [],
            "unsafe_patterns": [],
            "recovery_events": [],
            "cleanup_events": [],
            "archive_cleanup_events": []
        }

    def _initialize_memory(self):

        self._save_memory(self._default_memory())

    def _ensure_memory_schema(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:

        default_memory = self._default_memory()

        for key, value in default_memory.items():

            if key not in data:
                data[key] = value

        return data

    def _create_corrupted_backup(self):

        if not os.path.exists(self.memory_file):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_file = os.path.join(
            self.backup_directory,
            f"corrupted_memory_{timestamp}.json"
        )

        shutil.copy2(self.memory_file, backup_file)

        return backup_file

    def _create_memory_archive(
        self,
        reason: str
    ):

        if not os.path.exists(self.memory_file):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        archive_file = os.path.join(
            self.archive_directory,
            f"memory_archive_{reason}_{timestamp}.json"
        )

        shutil.copy2(self.memory_file, archive_file)

        return archive_file

    def _recover_memory(self) -> Dict[str, Any]:

        backup_file = self._create_corrupted_backup()

        recovered_memory = self._default_memory()

        recovered_memory["recovery_events"].append(
            {
                "event": "Corrupted memory recovered",
                "timestamp": datetime.now().isoformat(),
                "session_id": str(uuid.uuid4()),
                "backup_file": backup_file
            }
        )

        self._save_memory(recovered_memory)

        return recovered_memory

    def _load_memory(self) -> Dict[str, Any]:

        try:

            with open(self.memory_file, "r") as file:
                data = json.load(file)

            data = self._ensure_memory_schema(data)

            return data

        except JSONDecodeError:

            return self._recover_memory()

        except FileNotFoundError:

            self._initialize_memory()

            with open(self.memory_file, "r") as file:
                return json.load(file)

    def _save_memory(
        self,
        data: Dict[str, Any]
    ):

        with open(self.memory_file, "w") as file:
            json.dump(data, file, indent=4)

    def _cleanup_memory(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:

        data = self._ensure_memory_schema(data)

        cleanup_actions = []

        if len(data["approved_decisions"]) > self.max_approved_decisions:

            self._create_memory_archive("approved_decisions_limit")

            removed_count = (
                len(data["approved_decisions"])
                - self.max_approved_decisions
            )

            data["approved_decisions"] = data["approved_decisions"][
                -self.max_approved_decisions:
            ]

            cleanup_actions.append(
                f"Trimmed approved_decisions by {removed_count}"
            )

        if len(data["recovery_events"]) > self.max_recovery_events:

            removed_count = (
                len(data["recovery_events"])
                - self.max_recovery_events
            )

            data["recovery_events"] = data["recovery_events"][
                -self.max_recovery_events:
            ]

            cleanup_actions.append(
                f"Trimmed recovery_events by {removed_count}"
            )

        if len(data["cleanup_events"]) > self.max_cleanup_events:
            
            data["cleanup_events"] = data["cleanup_events"][
                -self.max_cleanup_events:
            ]
        
        if (
                len(data["archive_cleanup_events"])
                > self.max_archive_cleanup_events
            ):

                data["archive_cleanup_events"] = (
                    data["archive_cleanup_events"][
                        -self.max_archive_cleanup_events:
                ]
            )

        if cleanup_actions:

            data["cleanup_events"].append(
                {
                    "event": "Memory cleanup enforced",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": str(uuid.uuid4()),
                    "actions": cleanup_actions
                }
            )
            
        self._prune_old_archives(data)
        
        return data

    def enforce_cleanup(self) -> Dict[str, Any]:

        data = self._load_memory()
        cleaned_data = self._cleanup_memory(data)
        self._save_memory(cleaned_data)

        return {
            "success": True,
            "message": "Memory cleanup enforcement completed.",
            "memory": cleaned_data
        }

    def _approved_decision_exists(
        self,
        data: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> bool:

        new_decision = decision.get("decision")
        new_risk_level = decision.get("risk_level")

        for existing_decision in data.get("approved_decisions", []):

            if (
                existing_decision.get("decision") == new_decision
                and existing_decision.get("risk_level") == new_risk_level
            ):
                return True

        return False

    def store_approved_decision(
        self,
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:

        data = self._load_memory()

        if self._approved_decision_exists(data, decision):

            return {
                "success": False,
                "stored": False,
                "duplicate": True,
                "message": (
                    "Duplicate approved decision "
                    "detected. Memory write skipped."
                )
            }

        enhanced_decision = {
            "decision": decision["decision"],
            "risk_level": decision["risk_level"],
            "timestamp": datetime.now().isoformat(),
            "session_id": str(uuid.uuid4())
        }

        data["approved_decisions"].append(enhanced_decision)

        data = self._cleanup_memory(data)

        self._save_memory(data)

        return {
            "success": True,
            "stored": True,
            "duplicate": False,
            "message": "Approved decision stored successfully.",
            "entry": enhanced_decision
        }
        
    def _prune_old_archives(
        self,
        data: Dict[str, Any],
    ):
    
        archive_files = []

        for file_name in os.listdir(
            self.archive_directory
        ):

            if (
                file_name.startswith(
                    "memory_archive_"
                )
                and
                file_name.endswith(".json")
            ):

                full_path = os.path.join(
                    self.archive_directory,
                    file_name
                )

                archive_files.append(full_path)

        archive_files = sorted(
            archive_files,
            key=os.path.getmtime
        )

        if (
            len(archive_files)
            <= self.max_archive_files
        ):
            return

        files_to_remove = (
            len(archive_files)
            - self.max_archive_files
        )

        removed_files = []

        for file_path in archive_files[
            :files_to_remove
        ]:

            removed_files.append(
                os.path.basename(file_path)
            )

            try:
                os.remove(file_path)
            except OSError:
                pass

        data[
            "archive_cleanup_events"
        ].append(
            {
                "event":
                (
                    "Archive retention "
                    "cleanup enforced"
                ),
                "timestamp":
                datetime.now().isoformat(),
                "session_id":
                str(uuid.uuid4()),
                "removed_archives":
                removed_files
            }
        )    

    def get_memory(self) -> Dict[str, Any]:

        return self._load_memory()