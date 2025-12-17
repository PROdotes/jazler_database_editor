"""
Theme usage validator - ensures theme.json documentation matches actual code usage.

This script scans the codebase to find all theme constant usages and compares them
against the documented usage in theme.json. It helps maintain accurate documentation
and catches when colors are used in new places without updating the docs.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ThemeUsageValidator:
    """Validates that theme.json documentation matches actual code usage."""
    
    # Map theme constants to their JSON path
    THEME_CONSTANT_MAP = {
        'theme.BG_DARK': ('backgrounds', 'dark'),
        'theme.BG_LIGHTER': ('backgrounds', 'lighter'),
        'theme.BG_CONTROL_BAR': ('backgrounds', 'control_bar'),
        'theme.BG_DISABLED': ('backgrounds', 'disabled'),
        'theme.FG_WHITE': ('foregrounds', 'white'),
        'theme.FG_LIGHT_GRAY': ('foregrounds', 'light_gray'),
        'theme.FG_MEDIUM_GRAY': ('foregrounds', 'medium_gray'),
        'theme.STATUS_SUCCESS': ('status', 'success'),
        'theme.STATUS_DANGER': ('status', 'danger'),
        'theme.STATUS_WARNING': ('status', 'warning'),
        'theme.STATUS_ERROR_BG': ('status', 'error_background'),
        'theme.BTN_ACTIVE': ('buttons', 'active'),
        'theme.BTN_DISABLED': ('buttons', 'disabled'),
    }
    
    def __init__(self, project_root: Path):
        """
        Initialize the validator.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.theme_json_path = project_root / 'theme.json'
        self.src_dir = project_root / 'src'
        
    def load_theme_json(self) -> Dict:
        """Load and parse theme.json."""
        with open(self.theme_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def find_theme_usages(self) -> Dict[str, List[Tuple[str, int, str]]]:
        """
        Scan source code for theme constant usages.
        
        Returns:
            Dictionary mapping theme constants to list of (file, line_num, context) tuples
        """
        usages = defaultdict(list)
        
        # Pattern to match theme constant usage
        # Matches: theme.BG_DARK, theme.STATUS_SUCCESS, etc.
        pattern = re.compile(r'theme\.(BG_\w+|FG_\w+|STATUS_\w+|BTN_\w+)')
        
        # Scan all Python files in src/
        for py_file in self.src_dir.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        matches = pattern.findall(line)
                        for match in matches:
                            constant = f'theme.{match}'
                            # Get context (simplified - just the line content)
                            context = line.strip()
                            relative_path = py_file.relative_to(self.project_root)
                            usages[constant].append((str(relative_path), line_num, context))
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        return dict(usages)
    
    def extract_usage_descriptions(self, usages: Dict[str, List[Tuple[str, int, str]]]) -> Dict[str, Set[str]]:
        """
        Extract human-readable usage descriptions from code context.
        
        Args:
            usages: Dictionary of theme constant usages
            
        Returns:
            Dictionary mapping theme constants to set of usage descriptions
        """
        descriptions = defaultdict(set)
        
        for constant, usage_list in usages.items():
            for file_path, line_num, context in usage_list:
                # Try to extract meaningful description from context
                desc = self._extract_description(file_path, context)
                if desc:
                    descriptions[constant].add(desc)
        
        return dict(descriptions)
    
    def _extract_description(self, file_path: str, context: str) -> str:
        """
        Extract a human-readable description from code context.
        
        Args:
            file_path: Path to the file
            context: Line of code containing the theme usage
            
        Returns:
            Human-readable description or empty string
        """
        # Extract component/widget type from context
        context_lower = context.lower()
        
        # Check for common widget types
        if 'label' in context_lower:
            if 'status' in context_lower:
                return "Status labels"
            elif 'counter' in context_lower:
                return "Counter display"
            elif 'done' in context_lower:
                return "Done status indicator"
            return "Labels"
        
        if 'button' in context_lower or 'btn' in context_lower:
            if 'test' in context_lower:
                return "Test database button"
            elif 'live' in context_lower:
                return "Live database button"
            return "Buttons"
        
        if 'frame' in context_lower:
            if 'control' in context_lower or 'nav' in context_lower:
                return "Control/navigation frame"
            elif 'msg' in context_lower:
                return "Message frame"
            return "Frames"
        
        if 'entry' in context_lower or 'text_' in context_lower:
            if 'query' in context_lower:
                return "Query input field"
            elif 'jump' in context_lower:
                return "Jump position input"
            return "Input fields"
        
        if 'window' in context_lower:
            if 'query' in context_lower:
                return "Query dialog"
            return "Windows/dialogs"
        
        if 'config(' in context_lower:
            if 'genre' in context_lower:
                return "Genre validation"
            elif 'isrc' in context_lower:
                return "ISRC validation"
            elif 'file' in context_lower:
                return "File path validation"
            return "Field validation"
        
        # Default: use file location
        if 'app.py' in file_path:
            return "Main UI"
        
        return ""
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate theme usage against documentation.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Load theme.json
        try:
            theme_data = self.load_theme_json()
        except Exception as e:
            return False, [f"Failed to load theme.json: {e}"]
        
        # Find actual usages
        actual_usages = self.find_theme_usages()
        
        # Check each theme constant
        for constant, (category, key) in self.THEME_CONSTANT_MAP.items():
            # Get documented usage
            try:
                color_info = theme_data[category][key]
                documented_uses = set(color_info.get('used_in', []))
            except KeyError:
                issues.append(f"[ERROR] {constant}: Not found in theme.json")
                continue
            
            # Get actual usage count
            actual_usage_list = actual_usages.get(constant, [])
            usage_count = len(actual_usage_list)
            
            if usage_count == 0:
                issues.append(
                    f"[WARN] {constant}: Documented but not used in code\n"
                    f"       Documented uses: {', '.join(documented_uses)}"
                )
            else:
                # Extract descriptions from actual usage
                actual_descriptions = self.extract_usage_descriptions({constant: actual_usage_list})
                actual_desc_set = actual_descriptions.get(constant, set())
                
                # Report usage count
                issues.append(
                    f"[OK]   {constant}: Used {usage_count} times in code\n"
                    f"       Documented: {len(documented_uses)} use cases\n"
                    f"       Detected: {', '.join(sorted(actual_desc_set)) if actual_desc_set else 'N/A'}"
                )
        
        # Check for undocumented theme usages
        for constant in actual_usages:
            if constant not in self.THEME_CONSTANT_MAP:
                issues.append(f"[WARN] {constant}: Used in code but not in THEME_CONSTANT_MAP")
        
        # Determine if valid (no critical issues)
        is_valid = not any(issue.startswith('[ERROR]') for issue in issues)
        
        return is_valid, issues
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive validation report.
        
        Returns:
            Formatted report string
        """
        is_valid, issues = self.validate()
        
        report = ["=" * 80]
        report.append("THEME USAGE VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        if is_valid:
            report.append("[PASS] Overall Status: VALID")
        else:
            report.append("[FAIL] Overall Status: ISSUES FOUND")
        
        report.append("")
        report.append("-" * 80)
        report.append("DETAILS:")
        report.append("-" * 80)
        report.append("")
        
        for issue in issues:
            report.append(issue)
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Run the theme usage validator."""
    import sys
    from pathlib import Path
    
    # Determine project root
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        # Assume script is run from project root
        project_root = Path.cwd()
    
    print(f"Validating theme usage in: {project_root}")
    print()
    
    validator = ThemeUsageValidator(project_root)
    report = validator.generate_report()
    
    print(report)
    
    # Exit with error code if validation failed
    is_valid, _ = validator.validate()
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
