import unittest
from pathlib import Path

from src.data.m1 import (
    assign_group_splits,
    duplicate_clusters,
    duplicate_split_violations,
    parse_dlc_inventory,
    parse_sidtd_template_names,
    validate_manifest,
)


class M1DataTests(unittest.TestCase):
    def test_split_is_deterministic_and_group_safe(self) -> None:
        groups = [f"g{i}" for i in range(80)]
        self.assertEqual(assign_group_splits(groups), assign_group_splits(list(reversed(groups))))
        self.assertEqual(set(assign_group_splits(groups).values()), {"train", "validation", "test"})

    def test_dlc_inventory_counts(self) -> None:
        path = Path(__file__).parents[1] / "data" / "raw" / "source_metadata" / "dlc2021" / "dlc-2021.csv"
        records = parse_dlc_inventory(path)
        report = validate_manifest(records)
        self.assertTrue(report["valid"])
        self.assertEqual(report["sample_count"], 1424)
        self.assertEqual(report["base_document_count"], 80)
        self.assertEqual(report["counts_by_class"], {"BONA_FIDE": 290, "PRINT": 734, "SCREEN": 400})

    def test_sidtd_fake_and_real_share_lineage(self) -> None:
        names = [
            "templates/Images/reals/alb_id_00.jpg",
            "templates/Images/fakes/alb_id_00_fake_6_25.jpg",
        ]
        records = parse_sidtd_template_names(names)
        self.assertEqual({record.base_document_id for record in records}, {"sidtd:alb_id:00"})
        self.assertEqual(len({record.split for record in records}), 1)

    def test_duplicate_split_isolation(self) -> None:
        records = [
            {"sha256": "a", "phash": "0000000000000000", "split": "train"},
            {"sha256": "b", "phash": "0000000000000001", "split": "test"},
        ]
        clusters = duplicate_clusters(records, max_phash_distance=1)
        self.assertEqual(len(duplicate_split_violations(records, clusters)), 1)


if __name__ == "__main__":
    unittest.main()
