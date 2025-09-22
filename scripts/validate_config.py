#!/usr/bin/env python3
"""
Validate Configuration Files

This script validates that all configuration files are properly formatted
and contain the expected structure for the PDF extraction pipeline.
"""

import sys
from pathlib import Path

# Try to import yaml, handle missing dependency gracefully
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("⚠️  Warning: PyYAML not available, using basic validation only")


def validate_yaml_file(file_path: Path) -> bool:
    """
    Validate that a YAML file is properly formatted and loadable.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not file_path.exists():
            print(f"❌ Configuration file not found: {file_path}")
            return False
        
        if HAS_YAML:
            # Full YAML validation with PyYAML
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                print(f"❌ Configuration file is empty: {file_path}")
                return False
            
            print(f"✅ Configuration file is valid YAML: {file_path}")
            
            # Show structure information
            if isinstance(config, dict):
                print(f"   📋 Found {len(config)} configuration sections:")
                for key in config.keys():
                    print(f"      - {key}")
            elif isinstance(config, list):
                print(f"   📋 Found {len(config)} configuration items")
            else:
                print(f"   📋 Configuration type: {type(config).__name__}")
        else:
            # Basic validation without PyYAML - just check file is readable
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                print(f"❌ Configuration file is empty: {file_path}")
                return False
            
            # Basic syntax checks
            lines = content.split('\n')
            has_content = False
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                has_content = True
                
                # Check for basic YAML structure indicators
                if ':' in line and not line.startswith('-'):
                    # Looks like a key-value pair
                    continue
                elif line.startswith('-'):
                    # Looks like a list item
                    continue
                else:
                    # Check for common YAML errors
                    if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                        print(f"❌ Possible quoting issue at line {line_num}: {line}")
                        return False
            
            if not has_content:
                print(f"❌ Configuration file appears to contain no content: {file_path}")
                return False
            
            print(f"✅ Configuration file appears valid (basic check): {file_path}")
            print(f"   📋 File contains {len([l for l in lines if l.strip() and not l.strip().startswith('#')])} non-empty lines")
        
        return True
        
    except Exception as e:
        if HAS_YAML and 'yaml' in str(e).lower():
            print(f"❌ YAML parsing error in {file_path}:")
            print(f"   {e}")
        else:
            print(f"❌ Error reading {file_path}:")
            print(f"   {e}")
        return False


def validate_all_configs() -> bool:
    """
    Validate all configuration files in the project.
    
    Returns:
        bool: True if all files are valid, False otherwise
    """
    config_files = [
        Path("config/extraction_config.yaml"),
        Path("dvc.yaml"),
        Path(".github/workflows/smoke-test.yml"),
    ]
    
    print("🔍 Validating configuration files...")
    print("=" * 50)
    
    all_valid = True
    
    for config_file in config_files:
        print(f"\n📄 Checking: {config_file}")
        
        if not validate_yaml_file(config_file):
            all_valid = False
        
        print()  # Add spacing between files
    
    # Summary
    print("=" * 50)
    if all_valid:
        print("🎉 All configuration files are valid!")
        return True
    else:
        print("❌ Some configuration files have errors!")
        return False


def main():
    """Main function to run configuration validation."""
    try:
        success = validate_all_configs()
        
        if not success:
            print("\n💡 Please fix the configuration errors before proceeding.")
            sys.exit(1)
        
        print("\n✅ Configuration validation completed successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()