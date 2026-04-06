import os
import tempfile
import unittest
import json
import yaml
from validate_scenarios import (
    is_valid_json, 
    is_valid_yaml, 
    get_target_files, 
    is_valid_json_content, 
    is_valid_yaml_content
)

class TestValidateScenarios(unittest.TestCase):
    """Simple test harness for validate_scenarios scripts."""
    
    def test_is_valid_json_content(self):
        """Pure functional test for JSON content validation."""
        # Valid JSON
        is_valid, error = is_valid_json_content('{"key": "value"}')
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Invalid JSON - check for context snippet
        is_valid, error = is_valid_json_content('{"key": "value" missing quotes}')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("--- Potential Error Section ---", error)
        self.assertIn("   1 | >> {\"key\": \"value\" missing quotes}", error)

    def test_is_valid_yaml_content(self):
        """Pure functional test for YAML content validation."""
        # Valid YAML
        is_valid, error = is_valid_yaml_content('key: value\nlist:\n  - item')
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Invalid YAML - check for context snippet
        # Tab characters are often disallowed in YAML for indentation
        is_valid, error = is_valid_yaml_content('key: value\n\tlist: invalid')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("--- Potential Error Section ---", error)
        self.assertIn("   2 | >> \tlist: invalid", error)

    def test_is_valid_json_integration(self):
        """Integration test for JSON file validation."""
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
            f.write('{"key": "value"}')
            temp_path = f.name
        try:
            is_valid, error = is_valid_json(temp_path)
            self.assertTrue(is_valid)
        finally:
            os.remove(temp_path)

    def test_is_valid_yaml_integration(self):
        """Integration test for YAML file validation."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False) as f:
            f.write('key: value')
            temp_path = f.name
        try:
            is_valid, error = is_valid_yaml(temp_path)
            self.assertTrue(is_valid)
        finally:
            os.remove(temp_path)

    def test_get_target_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirs and various files
            subdir = os.path.join(temp_dir, 'subdir')
            os.makedirs(subdir)
            
            paths = [
                os.path.join(temp_dir, 'f1.json'),
                os.path.join(temp_dir, 'f2.yaml'),
                os.path.join(temp_dir, 'f3.txt'),
                os.path.join(subdir, 'f4.yml'),
            ]
            for p in paths:
                with open(p, 'w') as f:
                    f.write('content')
            
            target_files = get_target_files(temp_dir)
            filenames = [os.path.basename(f) for f in target_files]
            
            self.assertIn('f1.json', filenames)
            self.assertIn('f2.yaml', filenames)
            self.assertIn('f4.yml', filenames)
            self.assertNotIn('f3.txt', filenames)
            self.assertEqual(len(target_files), 3)

if __name__ == "__main__":
    unittest.main()
