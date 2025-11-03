#!/usr/bin/env python3
"""
Unit Tests for Amendment Parser
Comprehensive test coverage for all parsing functions
"""

import unittest
import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from amendment_parser import AmendmentParser, ParsedAmendment, ParsedBGBl, ParsedFussnote


class TestAmendmentParser(unittest.TestCase):
    """Test suite for AmendmentParser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = AmendmentParser()
    
    # ========== Tests for parse_standkommentar() ==========
    
    def test_parse_standard_last_amended(self):
        """Test parsing standard 'last amended' text"""
        text = "Zuletzt geändert durch Art. 66 G v. 23.10.2024 I Nr. 323"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.amendment_type, 'last_amended')
        self.assertEqual(result.amendment_date, date(2024, 10, 23))
        self.assertEqual(result.artikel, 'Art. 66')
        self.assertEqual(result.gesetz_ref, 'G v. 23.10.2024 I Nr. 323')
        self.assertEqual(result.bgbl_issue, 'Nr. 323')
        self.assertEqual(result.bgbl_year, '2024')
    
    def test_parse_reissued(self):
        """Test parsing 'reissued' (Neugefasst) text"""
        text = "Neugefasst durch Bek. v. 19.2.2002 I 754, 1404, 3384"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.amendment_type, 'reissued')
        self.assertEqual(result.amendment_date, date(2002, 2, 19))
    
    def test_parse_indirect_amendment(self):
        """Test parsing indirect amendment"""
        text = "Mittelbare Änderung durch Art. 154a Nr. 3 Buchst. a G v. 20.11.2019 I 1626"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.amendment_type, 'indirect_amendment')
        self.assertEqual(result.amendment_date, date(2019, 11, 20))
        self.assertEqual(result.artikel, 'Art. 154a')
    
    def test_parse_supplement(self):
        """Test parsing supplement (Ergänzung)"""
        text = "Ergänzung aufgrund der Verordnung v. 25.11.2024 I Nr. 365"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.amendment_type, 'supplement')
        self.assertEqual(result.amendment_date, date(2024, 11, 25))
    
    def test_parse_multiple_dates(self):
        """Test handling text with multiple dates (should extract first)"""
        text = "Neugefasst durch Bek. v. 19.2.2002 I 754; zuletzt geändert durch Art. 11 G v. 18.12.2024 I Nr. 423"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        # Should extract first date
        self.assertEqual(result.amendment_date, date(2002, 2, 19))
    
    def test_parse_with_artikel_variants(self):
        """Test parsing different Artikel formats"""
        test_cases = [
            ("Art. 66", "Art. 66"),
            ("Art.66", "Art. 66"),
            ("Art 66", "Art. 66"),
            ("Art. 154a", "Art. 154a"),
        ]
        
        for input_art, expected_art in test_cases:
            text = f"Zuletzt geändert durch {input_art} G v. 23.10.2024"
            result = self.parser.parse_standkommentar(text)
            self.assertEqual(result.artikel, expected_art, f"Failed for input: {input_art}")
    
    def test_parse_single_digit_day_month(self):
        """Test parsing dates with single-digit day/month"""
        text = "Zuletzt geändert durch G v. 5.3.2024"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.amendment_date, date(2024, 3, 5))
    
    def test_parse_no_artikel(self):
        """Test parsing text without Artikel"""
        text = "Zuletzt geändert durch G v. 23.10.2024 I Nr. 323"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertIsNone(result.artikel)
        self.assertEqual(result.gesetz_ref, 'G v. 23.10.2024 I Nr. 323')
    
    def test_parse_empty_string(self):
        """Test handling empty string"""
        result = self.parser.parse_standkommentar("")
        self.assertIsNone(result)
    
    def test_parse_none(self):
        """Test handling None input"""
        result = self.parser.parse_standkommentar(None)
        self.assertIsNone(result)
    
    def test_parse_invalid_date(self):
        """Test handling invalid date (should still create result)"""
        text = "Zuletzt geändert durch Art. 66 G v. 99.99.2024"
        result = self.parser.parse_standkommentar(text)
        
        # Should still parse other fields
        self.assertIsNotNone(result)
        self.assertEqual(result.artikel, 'Art. 66')
        # Date should be None due to invalid date
        self.assertIsNone(result.amendment_date)
    
    def test_extract_all_amendments(self):
        """Test extracting multiple amendments from text"""
        text = "Zuletzt geändert durch Art. 11 G v. 18.12.2024 I Nr. 423; Neugefasst durch Bek. v. 19.2.2002 I 754"
        results = self.parser.extract_all_amendments_from_text(text)
        
        self.assertEqual(len(results), 2)
        # Should be sorted by date (most recent first)
        self.assertEqual(results[0].amendment_date, date(2024, 12, 18))
        self.assertEqual(results[1].amendment_date, date(2002, 2, 19))
    
    # ========== Tests for parse_fussnote() ==========
    
    def test_parse_fussnote_with_valid_from(self):
        """Test parsing fussnote with 'ab' date"""
        text = "(+++ Textnachweis ab: 21.8.1996 +++)"
        result = self.parser.parse_fussnote(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.valid_from, date(1996, 8, 21))
        self.assertIn("Textnachweis", result.context)
    
    def test_parse_fussnote_with_in_kraft(self):
        """Test parsing fussnote with 'in Kraft' date"""
        text = "Das Gesetz tritt in Kraft am 1.1.2011"
        result = self.parser.parse_fussnote(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.in_kraft, date(2011, 1, 1))
    
    def test_parse_fussnote_with_both_dates(self):
        """Test parsing fussnote with both valid_from and in_kraft"""
        text = "Textnachweis ab: 21.8.1996, in Kraft getreten am 1.1.1997"
        result = self.parser.parse_fussnote(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.valid_from, date(1996, 8, 21))
        self.assertEqual(result.in_kraft, date(1997, 1, 1))
    
    def test_parse_fussnote_no_dates(self):
        """Test parsing fussnote without dates (should return None)"""
        text = "This is just some general information without dates"
        result = self.parser.parse_fussnote(text)
        
        self.assertIsNone(result)
    
    def test_parse_fussnote_empty(self):
        """Test handling empty fussnote"""
        result = self.parser.parse_fussnote("")
        self.assertIsNone(result)
    
    def test_parse_fussnote_context_truncation(self):
        """Test that context is truncated to 300 chars"""
        long_text = "a" * 500 + " ab: 21.8.1996"
        result = self.parser.parse_fussnote(long_text)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.context), 300)
    
    # ========== Tests for parse_bgbl_reference() ==========
    
    def test_parse_bgbl_standard(self):
        """Test parsing standard BGBl reference"""
        result = self.parser.parse_bgbl_reference("BGBl I", "1996, 1254")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "bgbl_1996_1254")
        self.assertEqual(result.periodikum, "BGBl I")
        self.assertEqual(result.year, "1996")
        self.assertEqual(result.page, "1254")
        self.assertEqual(result.full_reference, "BGBl I 1996, 1254")
    
    def test_parse_bgbl_type_2(self):
        """Test parsing BGBl II reference"""
        result = self.parser.parse_bgbl_reference("BGBl II", "2020, 567")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.periodikum, "BGBl II")
        self.assertEqual(result.year, "2020")
        self.assertEqual(result.page, "567")
    
    def test_parse_bgbl_with_spaces(self):
        """Test parsing BGBl with extra spaces"""
        result = self.parser.parse_bgbl_reference("BGBl I", "1996,  1254")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, "1996")
        self.assertEqual(result.page, "1254")
    
    def test_parse_bgbl_invalid_format(self):
        """Test handling invalid BGBl format"""
        result = self.parser.parse_bgbl_reference("BGBl I", "invalid")
        self.assertIsNone(result)
    
    def test_parse_bgbl_empty(self):
        """Test handling empty BGBl inputs"""
        result = self.parser.parse_bgbl_reference("", "")
        self.assertIsNone(result)
        
        result = self.parser.parse_bgbl_reference("BGBl I", "")
        self.assertIsNone(result)
    
    # ========== Tests for to_dict() methods ==========
    
    def test_parsed_amendment_to_dict(self):
        """Test ParsedAmendment.to_dict()"""
        text = "Zuletzt geändert durch Art. 66 G v. 23.10.2024 I Nr. 323"
        parsed = self.parser.parse_standkommentar(text)
        result = parsed.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['amendment_date'], '2024-10-23')
        self.assertEqual(result['artikel'], 'Art. 66')
        self.assertEqual(result['raw_text'], text)
    
    def test_parsed_fussnote_to_dict(self):
        """Test ParsedFussnote.to_dict()"""
        text = "Textnachweis ab: 21.8.1996"
        parsed = self.parser.parse_fussnote(text)
        result = parsed.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['valid_from'], '1996-08-21')
        self.assertIsNone(result['in_kraft'])
    
    def test_parsed_bgbl_to_dict(self):
        """Test ParsedBGBl.to_dict()"""
        parsed = self.parser.parse_bgbl_reference("BGBl I", "1996, 1254")
        result = parsed.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 'bgbl_1996_1254')
        self.assertEqual(result['full_reference'], 'BGBl I 1996, 1254')
    
    # ========== Integration Tests ==========
    
    def test_real_world_example_1(self):
        """Test with real example from SGB VII"""
        text = "Zuletzt geändert durch Art. 66 G v. 23.10.2024 I Nr. 323"
        result = self.parser.parse_standkommentar(text)
        
        self.assertEqual(result.amendment_type, 'last_amended')
        self.assertEqual(result.amendment_date, date(2024, 10, 23))
        self.assertEqual(result.artikel, 'Art. 66')
        self.assertEqual(result.bgbl_issue, 'Nr. 323')
    
    def test_real_world_example_2(self):
        """Test with real reissued example"""
        text = "Neugefasst durch Bek. v. 19.2.2002 I 754, 1404, 3384"
        result = self.parser.parse_standkommentar(text)
        
        self.assertEqual(result.amendment_type, 'reissued')
        self.assertEqual(result.amendment_date, date(2002, 2, 19))
    
    def test_real_world_example_3(self):
        """Test with real example containing mittelbare Änderung"""
        text = "Mittelbare Änderung durch Art. 15 Nr. 3 G v. 18.12.2024 I Nr. 423 ist berücksichtigt"
        result = self.parser.parse_standkommentar(text)
        
        self.assertEqual(result.amendment_type, 'indirect_amendment')
        self.assertEqual(result.amendment_date, date(2024, 12, 18))
        self.assertEqual(result.artikel, 'Art. 15')


class TestAmendmentParserEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = AmendmentParser()
    
    def test_very_long_text(self):
        """Test handling very long amendment text"""
        long_text = "a" * 1000 + " Zuletzt geändert durch Art. 66 G v. 23.10.2024"
        result = self.parser.parse_standkommentar(long_text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.artikel, 'Art. 66')
    
    def test_special_characters(self):
        """Test handling special characters in text"""
        text = "Zuletzt geändert durch Art. 66 § G v. 23.10.2024 € I Nr. 323"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.artikel, 'Art. 66')
    
    def test_unicode_characters(self):
        """Test handling Unicode characters"""
        text = "Zuletzt geändert durch Art. 66 G v. 23.10.2024 — I Nr. 323"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.artikel, 'Art. 66')
    
    def test_multiple_artikel_references(self):
        """Test text with multiple Artikel (should extract first)"""
        text = "Zuletzt geändert durch Art. 66 und Art. 67 G v. 23.10.2024"
        result = self.parser.parse_standkommentar(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.artikel, 'Art. 66')


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAmendmentParser))
    suite.addTests(loader.loadTestsFromTestCase(TestAmendmentParserEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("="*70)
    print("Amendment Parser Unit Tests")
    print("="*70)
    print()
    
    result = run_tests()
    
    print()
    print("="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
