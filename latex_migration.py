"""
LaTeX Template Migration Script
================================
Transfers content from old LaTeX template to new template based on section mapping
and inserts new content for additional sections.
"""

import re
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import shutil


class LaTeXMigrator:
    """Handles migration of content between LaTeX templates."""
    
    def __init__(self, config_file: str, verbose: bool = False):
        """
        Initialize the migrator with configuration.
        
        Args:
            config_file: Path to JSON configuration file
            verbose: Enable verbose logging
        """
        self.setup_logging(verbose)
        self.config = self.load_config(config_file)
        self.sections_pattern = self._compile_section_patterns()
        
    def setup_logging(self, verbose: bool):
        """Configure logging."""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_file}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _compile_section_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for different LaTeX section types."""
        patterns = {
            'chapter': re.compile(r'\\chapter(\*?)\{([^}]+)\}'),
            'section': re.compile(r'\\section(\*?)\{([^}]+)\}'),
            'subsection': re.compile(r'\\subsection(\*?)\{([^}]+)\}'),
            'subsubsection': re.compile(r'\\subsubsection(\*?)\{([^}]+)\}'),
            'paragraph': re.compile(r'\\paragraph(\*?)\{([^}]+)\}'),
        }
        return patterns
    
    def _get_section_level_rank(self, level: str) -> int:
        """Get numeric rank for section hierarchy (lower = higher in hierarchy)."""
        ranks = {
            'chapter': 0,
            'section': 1,
            'subsection': 2,
            'subsubsection': 3,
            'paragraph': 4
        }
        return ranks.get(level, 999)
    
    def extract_sections_hierarchical(self, latex_content: str) -> Dict[str, Dict]:
        """
        Extract sections with hierarchical structure preserved.
        
        Returns:
            Dictionary mapping section titles to their content, metadata, and children
        """
        lines = latex_content.split('\n')
        sections = {}
        stack = []  # Stack to track hierarchy: [(title, level, start_line_idx)]
        
        for idx, line in enumerate(lines):
            # Check if line contains a section command
            section_found = False
            for level, pattern in self.sections_pattern.items():
                match = pattern.search(line)
                if match:
                    section_title = match.group(2).strip()
                    section_level = level
                    current_rank = self._get_section_level_rank(section_level)
                    
                    # Close all sections at same or lower hierarchy level
                    while stack and self._get_section_level_rank(stack[-1][1]) >= current_rank:
                        stack.pop()
                    
                    # Add to stack
                    stack.append((section_title, section_level, idx))
                    
                    # Initialize section entry if not exists
                    if section_title not in sections:
                        sections[section_title] = {
                            'level': section_level,
                            'line': line.strip(),
                            'content_lines': [],
                            'full_hierarchy': [s[0] for s in stack],  # Path from root
                            'parent': stack[-2][0] if len(stack) > 1 else None
                        }
                    
                    section_found = True
                    self.logger.debug(f"Found {section_level}: {section_title} (hierarchy: {' > '.join([s[0] for s in stack])})")
                    break
            
            # Add content to all active sections in stack
            if not section_found and stack:
                for section_title, _, _ in stack:
                    if section_title in sections:
                        sections[section_title]['content_lines'].append(line)
        
        # Convert content_lines to string and extract full hierarchical content
        for title, data in sections.items():
            data['content'] = '\n'.join(data['content_lines'])
            del data['content_lines']  # Clean up temporary field
        
        self.logger.info(f"Extracted {len(sections)} sections with hierarchical structure")
        return sections
    
    def extract_sections_content_only(self, latex_content: str) -> Dict[str, Dict]:
        """
        Extract sections with ONLY their direct content (excluding children).
        This is useful for granular mapping where subsections need separate mapping.
        
        Returns:
            Dictionary mapping section titles to their direct content only
        """
        lines = latex_content.split('\n')
        all_sections = []
        
        # Identify all section boundaries
        for idx, line in enumerate(lines):
            for level, pattern in self.sections_pattern.items():
                match = pattern.search(line)
                if match:
                    section_title = match.group(2).strip()
                    all_sections.append({
                        'title': section_title,
                        'level': level,
                        'rank': self._get_section_level_rank(level),
                        'line_idx': idx,
                        'line': line.strip()
                    })
                    break
        
        # Extract ONLY direct content (stop at any child section)
        sections = {}
        for i, section in enumerate(all_sections):
            title = section['title']
            start_idx = section['line_idx']
            current_rank = section['rank']
            
            # Find first child section (any section with lower rank = deeper level)
            end_idx = len(lines)
            for next_section in all_sections[i+1:]:
                # Stop at ANY section (including children)
                end_idx = next_section['line_idx']
                break
            
            # Extract only direct content
            direct_content = '\n'.join(lines[start_idx+1:end_idx])
            
            sections[title] = {
                'content': direct_content.strip(),
                'level': section['level'],
                'line': section['line'],
                'rank': current_rank
            }
            
            self.logger.debug(f"Extracted (content only) {section['level']}: {title}")
        
        self.logger.info(f"Extracted {len(sections)} sections (content-only mode)")
        return sections
    
    def extract_sections(self, latex_content: str) -> Dict[str, Dict]:
        """
        Extract sections and their FULL hierarchical content from LaTeX file.
        A parent section's content includes all its subsections, subsubsections, etc.
        
        Returns:
            Dictionary mapping section titles to their complete hierarchical content
        """
        lines = latex_content.split('\n')
        all_sections = []  # List of (title, level, start_idx, content_start_idx)
        
        # First pass: identify all section boundaries
        for idx, line in enumerate(lines):
            for level, pattern in self.sections_pattern.items():
                match = pattern.search(line)
                if match:
                    section_title = match.group(2).strip()
                    all_sections.append({
                        'title': section_title,
                        'level': level,
                        'rank': self._get_section_level_rank(level),
                        'line_idx': idx,
                        'line': line.strip()
                    })
                    break
        
        # Second pass: extract content for each section including all children
        sections = {}
        for i, section in enumerate(all_sections):
            title = section['title']
            start_idx = section['line_idx']
            current_rank = section['rank']
            
            # Find end of this section (next section at same or higher level)
            end_idx = len(lines)
            for next_section in all_sections[i+1:]:
                if next_section['rank'] <= current_rank:
                    end_idx = next_section['line_idx']
                    break
            
            # Extract full content including all children
            full_content = '\n'.join(lines[start_idx+1:end_idx])
            
            sections[title] = {
                'content': full_content.strip(),
                'level': section['level'],
                'line': section['line'],
                'rank': current_rank
            }
            
            self.logger.debug(f"Extracted {section['level']}: {title} (lines {start_idx+1}-{end_idx})")
        
        self.logger.info(f"Extracted {len(sections)} sections from old template")
        return sections
    
    def read_template(self, file_path: str) -> str:
        """Read LaTeX template file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.info(f"Read template: {file_path}")
            return content
        except FileNotFoundError:
            self.logger.error(f"Template file not found: {file_path}")
            raise
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            self.logger.warning(f"Used latin-1 encoding for {file_path}")
            return content
    
    def find_section_in_template(self, template_content: str, section_title: str, include_children: bool = True) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Find the start and end positions of a section in the template.
        
        Args:
            template_content: The template content to search in
            section_title: The title of the section to find
            include_children: If True, includes child sections in range. If False, stops at first child.
        
        Returns:
            Tuple of (start_pos, end_pos, section_level) or (None, None, None) if not found
        """
        # Create pattern for this specific section (now includes paragraph)
        patterns = [
            (rf'\\chapter\*?\{{{re.escape(section_title)}\}}', 'chapter'),
            (rf'\\section\*?\{{{re.escape(section_title)}\}}', 'section'),
            (rf'\\subsection\*?\{{{re.escape(section_title)}\}}', 'subsection'),
            (rf'\\subsubsection\*?\{{{re.escape(section_title)}\}}', 'subsubsection'),
            (rf'\\paragraph\*?\{{{re.escape(section_title)}\}}', 'paragraph'),
        ]
        
        for pattern, level in patterns:
            match = re.search(pattern, template_content)
            if match:
                start_pos = match.end()
                current_rank = self._get_section_level_rank(level)
                self.logger.debug(f"Found section '{section_title}' ({level}) at position {match.start()}-{start_pos}")
                
                # Find the end of this section
                remaining_content = template_content[start_pos:]
                lines = remaining_content.split('\n')
                end_pos = len(template_content)  # Default to end of file
                
                for line_idx, line in enumerate(lines):
                    # Check for \end{document} - stop before it
                    if re.search(r'\\end\{document\}', line):
                        end_pos = start_pos + len('\n'.join(lines[:line_idx]))
                        self.logger.debug(f"Found \\end{{document}} for section '{section_title}' at line_idx {line_idx}, end_pos={end_pos}")
                        return start_pos, end_pos, level
                    
                    # Check for next section
                    for check_level, check_pattern in self.sections_pattern.items():
                        if check_pattern.search(line):
                            check_rank = self._get_section_level_rank(check_level)
                            
                            # Determine where to stop based on include_children flag
                            if include_children:
                                # Stop only at same or higher level (excludes children)
                                should_stop = check_rank <= current_rank
                            else:
                                # Stop at ANY next section (includes children)
                                should_stop = True
                            
                            if should_stop:
                                # Calculate actual position in original content
                                end_pos = start_pos + len('\n'.join(lines[:line_idx]))
                                return start_pos, end_pos, level
                
                return start_pos, end_pos, level
        
        return None, None, None
    
    def migrate_content(self, old_template_path: str, new_template_path: str, output_path: str):
        """
        Main migration function.
        
        Args:
            old_template_path: Path to old LaTeX template
            new_template_path: Path to new LaTeX template
            output_path: Path for output migrated template
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting LaTeX template migration")
        self.logger.info("=" * 60)
        
        # Create backup of new template
        backup_path = f"{new_template_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(new_template_path, backup_path)
        self.logger.info(f"Backup created: {backup_path}")
        
        # Read templates
        old_content = self.read_template(old_template_path)
        new_content = self.read_template(new_template_path)
        
        # Get mapping mode from config (default: 'full_hierarchy')
        # 'full_hierarchy': Maps section with all children
        # 'granular': Maps only direct content, allowing individual subsection mapping
        mapping_mode = self.config.get('mapping_mode', 'full_hierarchy')
        
        # Extract sections from old template based on mode
        if mapping_mode == 'granular':
            self.logger.info("Using GRANULAR mapping mode (content-only, map subsections individually)")
            old_sections = self.extract_sections_content_only(old_content)
        else:
            self.logger.info("Using FULL HIERARCHY mapping mode (includes all children)")
            old_sections = self.extract_sections(old_content)
        
        # Also extract sections from new template to determine structure for new sections
        self.logger.info("Extracting sections from new template for structure reference...")
        if mapping_mode == 'granular':
            new_sections = self.extract_sections_content_only(new_content)
        else:
            new_sections = self.extract_sections(new_content)
        
        # Get mapping and new content from config
        section_mapping = self.config.get('section_mapping', {})
        new_sections_content = self.config.get('new_sections_content', {})
        
        # Process each mapping
        self.logger.info("\nProcessing section mappings...")
        
        # First pass: collect all replacements with their positions
        replacements = []
        # In granular mode, stop at child sections; in full_hierarchy mode, include them
        include_children_in_search = (mapping_mode != 'granular')
        
        # Collect section mapping replacements
        for old_section, new_section in section_mapping.items():
            if old_section in old_sections:
                self.logger.info(f"Mapping: '{old_section}' -> '{new_section}'")
                self.logger.debug(f"  Old section level: {old_sections[old_section]['level']}")
                
                # Find the section in new template
                start_pos, end_pos, found_level = self.find_section_in_template(
                    new_content, new_section, include_children=include_children_in_search
                )
                
                if start_pos is not None:
                    # Get content from old section
                    content_to_insert = old_sections[old_section]['content'].strip()
                    
                    if not content_to_insert:
                        self.logger.warning(f"  ⚠ No content found for '{old_section}'")
                    
                    replacements.append({
                        'start': start_pos,
                        'end': end_pos,
                        'content': content_to_insert,
                        'old_section': old_section,
                        'new_section': new_section,
                        'type': 'section_mapping'
                    })
                    
                    if mapping_mode == 'granular':
                        self.logger.info(f"  ✓ Will transfer direct content only (children mapped separately)")
                    else:
                        self.logger.info(f"  ✓ Will transfer hierarchical content (includes all children)")
                    self.logger.debug(f"  Content length: {len(content_to_insert)} chars")
                    self.logger.debug(f"  Content preview: {content_to_insert[:100]}..." if len(content_to_insert) > 100 else f"  Content: {content_to_insert}")
                else:
                    self.logger.warning(f"Section '{new_section}' not found in new template")
            else:
                self.logger.warning(f"Section '{old_section}' not found in old template")
        
        # Collect new sections content replacements
        sections_to_create = []  # Track sections that need to be created
        if new_sections_content:
            self.logger.info("\nProcessing new sections content...")
            for section_title, content in new_sections_content.items():
                start_pos, end_pos, found_level = self.find_section_in_template(
                    new_content, section_title, include_children=include_children_in_search
                )
                
                if start_pos is not None:
                    self.logger.info(f"Adding content for new section: '{section_title}'")
                    
                    replacements.append({
                        'start': start_pos,
                        'end': end_pos,
                        'content': content.strip(),
                        'old_section': 'NEW_CONTENT',
                        'new_section': section_title,
                        'type': 'new_content'
                    })
                    self.logger.debug(f"  Content length: {len(content.strip())} chars")
                    self.logger.debug(f"  Will replace range [{start_pos}:{end_pos}]")
                    self.logger.debug(f"  Original content in range: {repr(new_content[start_pos:end_pos][:100])}")
                else:
                    self.logger.info(f"New section '{section_title}' not found in template - will create it")
                    sections_to_create.append({
                        'title': section_title,
                        'content': content.strip()
                    })
        
        # Second pass: apply replacements in reverse order (from end to start)
        # This ensures earlier replacements don't affect positions of later ones
        self.logger.info(f"\nApplying {len(replacements)} replacements in reverse order...")
        replacements.sort(key=lambda x: x['start'], reverse=True)
        
        # Log the order
        for i, r in enumerate(replacements):
            self.logger.debug(f"Order {i}: {r['new_section']} at [{r['start']}:{r['end']}]")
        
        migrated_content = new_content
        for idx, replacement in enumerate(replacements):
            before = migrated_content[:replacement['start']]
            after = migrated_content[replacement['end']:]
            migrated_content = f"{before}\n{replacement['content']}\n{after}"
            
            if replacement['type'] == 'section_mapping':
                self.logger.debug(f"{idx}. Applied: {replacement['old_section']} -> {replacement['new_section']} at pos {replacement['start']}")
            else:
                self.logger.debug(f"{idx}. Applied new content: {replacement['new_section']} at pos {replacement['start']}")
        
        # Create new sections that don't exist in template
        if sections_to_create:
            self.logger.info(f"\nCreating {len(sections_to_create)} new section(s) not found in template...")
            
            # Find position of \end{document}
            end_doc_match = re.search(r'\\end\{document\}', migrated_content)
            if end_doc_match:
                insert_pos = end_doc_match.start()
                
                # Build the new sections content
                new_sections_text = ""
                for section_info in sections_to_create:
                    section_title = section_info['title']
                    section_content = section_info['content']
                    
                    # Determine section level - priority: new template > old template > default to \section
                    section_level = 'section'
                    source = 'default'
                    
                    # First check new template (highest priority)
                    if section_title in new_sections:
                        section_level = new_sections[section_title]['level']
                        source = 'new template'
                    # Then check old template
                    elif section_title in old_sections:
                        section_level = old_sections[section_title]['level']
                        source = 'old template'
                    
                    # Create section with content
                    new_sections_text += f"\n\\{section_level}{{{section_title}}}\n{section_content}\n"
                    self.logger.info(f"  Created \\{section_level}{{{section_title}}} (level from {source})")
                
                # Insert before \end{document}
                migrated_content = (
                    migrated_content[:insert_pos] +
                    new_sections_text +
                    "\n" +
                    migrated_content[insert_pos:]
                )
                self.logger.info(f"  ✓ Inserted new sections before \\end{{document}}")
            else:
                self.logger.warning("Could not find \\end{document} to insert new sections")
        
        # Post-processing: Fix document end issues
        self.logger.info("\nPost-processing: Cleaning up document structure...")
        
        # Remove duplicate \end{document} if any
        end_doc_pattern = r'\\end\{document\}'
        matches = list(re.finditer(end_doc_pattern, migrated_content))
        if len(matches) > 1:
            self.logger.warning(f"Found {len(matches)} \\end{{document}} statements, keeping only the last one")
            # Keep only the last occurrence
            last_match = matches[-1]
            # Remove all others
            for match in matches[:-1]:
                migrated_content = migrated_content[:match.start()] + migrated_content[match.end():]
                self.logger.debug(f"  Removed duplicate at position {match.start()}")
            # Need to re-find the last one since positions shifted
            matches = list(re.finditer(end_doc_pattern, migrated_content))
            last_match = matches[-1] if matches else None
        elif len(matches) == 1:
            last_match = matches[0]
            self.logger.debug(f"Found 1 \\end{{document}} at position {last_match.start()}")
        else:
            last_match = None
            self.logger.warning("No \\end{document} found in output!")
        
        # Ensure all content is before \end{document}
        if last_match:
            # Check if there's any section content after \end{document}
            after_end = migrated_content[last_match.end():]
            # Look for any section commands after \end{document}
            section_after = re.search(r'\\(section|subsection|subsubsection|paragraph)(\*?)\{', after_end)
            if section_after:
                self.logger.warning(f"Found section content after \\end{{document}}, moving it before")
                # Move everything between \end{document} and EOF to before \end{document}
                before_end = migrated_content[:last_match.start()]
                content_after = after_end.strip()
                if content_after:
                    migrated_content = f"{before_end}\n{content_after}\n\n{migrated_content[last_match.start():last_match.end()]}\n"
                    self.logger.debug(f"  Moved {len(content_after)} chars before \\end{{document}}")
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migrated_content)
        
        self.logger.info(f"\nMigration completed successfully!")
        self.logger.info(f"Output written to: {output_path}")
        self.logger.info(f"Backup saved as: {backup_path}")
        
        # Generate migration report
        self.generate_report(old_sections, section_mapping, new_sections_content, output_path)
    
    def generate_report(self, old_sections: Dict, mapping: Dict, new_content: Dict, output_path: str):
        """Generate a migration report."""
        report_path = Path(output_path).with_suffix('.migration_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("LaTeX Template Migration Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Old Template Sections Found: {len(old_sections)}\n")
            f.write(f"Mappings Applied: {len(mapping)}\n")
            f.write(f"New Sections Added: {len(new_content)}\n\n")
            
            f.write("Section Mappings:\n")
            f.write("-" * 60 + "\n")
            for old_sec, new_sec in mapping.items():
                status = "✓" if old_sec in old_sections else "✗"
                f.write(f"{status} {old_sec:30} -> {new_sec}\n")
            
            f.write("\nNew Sections:\n")
            f.write("-" * 60 + "\n")
            for section in new_content.keys():
                f.write(f"  • {section}\n")
            
            f.write("\nAll Old Template Sections:\n")
            f.write("-" * 60 + "\n")
            for section, data in old_sections.items():
                f.write(f"  • {section} ({data['level']})\n")
        
        self.logger.info(f"Migration report generated: {report_path}")


def create_example_config():
    """Create an example configuration file."""
    example_config = {
        "section_mapping": {
            "Introduction": "Introduction",
            "Related Work": "Background and Related Work",
            "Methodology": "Methods",
            "Experiments": "Experimental Setup",
            "Results": "Results and Discussion",
            "Conclusion": "Conclusions"
        },
        "new_sections_content": {
            "Acknowledgments": "The authors would like to thank...",
            "Data Availability": "The data used in this study is available upon request.",
            "Ethics Statement": "This research complies with all relevant ethical guidelines.",
            "Author Contributions": "All authors contributed to the writing and review of this manuscript."
        }
    }
    
    config_path = "migration_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=4)
    
    print(f"Example configuration created: {config_path}")
    print("\nEdit this file to match your specific template structure:")
    print("  - section_mapping: Maps old section names to new section names")
    print("  - new_sections_content: Content for sections that don't exist in old template")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Migrate content from old LaTeX template to new template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create example configuration file
  python latex_migration.py --create-config
  
  # Run migration
  python latex_migration.py -c config.json -o old.tex -n new.tex -out migrated.tex
  
  # Run with verbose output
  python latex_migration.py -c config.json -o old.tex -n new.tex -out migrated.tex -v
        """
    )
    
    parser.add_argument('--create-config', action='store_true',
                        help='Create an example configuration file')
    parser.add_argument('-c', '--config', type=str,
                        help='Path to configuration JSON file')
    parser.add_argument('-o', '--old-template', type=str,
                        help='Path to old LaTeX template')
    parser.add_argument('-n', '--new-template', type=str,
                        help='Path to new LaTeX template')
    parser.add_argument('-out', '--output', type=str,
                        help='Path for output migrated template')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_example_config()
        return
    
    if not all([args.config, args.old_template, args.new_template, args.output]):
        parser.error('--config, --old-template, --new-template, and --output are required '
                     '(or use --create-config to generate example configuration)')
    
    try:
        migrator = LaTeXMigrator(args.config, args.verbose)
        migrator.migrate_content(args.old_template, args.new_template, args.output)
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        raise


if __name__ == '__main__':
    main()
