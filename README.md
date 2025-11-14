# LaTeX Template Migration Tool

A Python-based tool for intelligently migrating content from old LaTeX templates to new ones, preserving hierarchical structure and supporting flexible section mappings.

## 🎯 Features

- **Two Migration Modes**:
  - **Granular Mode**: Maps individual sections and subsections independently (content-only)
  - **Hierarchical Mode**: Maps sections with all their children included
  
- **Intelligent Section Handling**:
  - Automatically maps content between different section hierarchies
  - Preserves section levels (chapter, section, subsection, subsubsection, paragraph)
  - Creates new sections that don't exist in the template
  
- **Flexible Configuration**:
  - JSON-based configuration for easy customization
  - Support for section renaming and restructuring
  - Add new content to sections not present in old template

- **Safety Features**:
  - Automatic backup creation before migration
  - Detailed logging and migration reports
  - Verbose mode for debugging

## 📋 Requirements

- Python 3.7+
- No external dependencies (uses Python standard library only)

## 🚀 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/latex-migration-tool.git
cd latex-migration-tool
```

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv myenv

# On Windows
myenv\Scripts\activate

# On macOS/Linux
source myenv/bin/activate
```

## 📖 Usage

### Basic Command

```bash
python latex_migration.py -c config.json -o old_template.tex -n new_template.tex -out output.tex
```

### Using Batch Files (Windows)

Double-click one of the provided batch files:
- `run_migration.bat` - Runs granular mode migration
- `run_migration_hierarchical.bat` - Runs hierarchical mode migration

### Command Line Arguments

```
-c, --config           Path to configuration JSON file (required)
-o, --old-template     Path to old LaTeX template (required)
-n, --new-template     Path to new LaTeX template (required)
-out, --output         Path for output migrated template (required)
-v, --verbose          Enable verbose output (optional)
```

## ⚙️ Configuration

Create a JSON configuration file with the following structure:

### Granular Mode Example

```json
{
    "mapping_mode": "granular",
    "section_mapping": {
        "Old Section Name": "New Section Name",
        "Model Description": "Methodology",
        "Architecture": "Model Architecture"
    },
    "new_sections_content": {
        "Acknowledgments": "We thank all contributors...",
        "Future Work": "We plan to extend this work..."
    }
}
```

### Hierarchical Mode Example

```json
{
    "mapping_mode": "full_hierarchy",
    "section_mapping": {
        "Introduction": "Introduction",
        "Related Work": "Background"
    },
    "new_sections_content": {
        "Acknowledgments": "We thank all contributors..."
    }
}
```

### Configuration Fields

- **`mapping_mode`**: 
  - `"granular"`: Maps only direct content, excludes children
  - `"full_hierarchy"`: Maps section with all nested subsections
  
- **`section_mapping`**: 
  - Key-value pairs mapping old section names to new section names
  - Supports mapping multiple old sections to the same new section
  
- **`new_sections_content`**: 
  - Content for sections not present in the old template
  - If section exists in new template, content replaces placeholder
  - If section doesn't exist, it's created before `\end{document}`

## 📊 How It Works

### Granular Mode (Content-Only)

```
Old Template:                    New Template:
└─ Section A                     └─ Section X
   ├─ Subsection A1        →        ├─ Subsection X1  (A1 content)
   └─ Subsection A2                 └─ Subsection X2  (A2 content)
```

Each subsection is mapped individually, allowing precise control.

### Hierarchical Mode (Full Tree)

```
Old Template:                    New Template:
└─ Section A                     └─ Section X
   ├─ Subsection A1        →        (All A's content including
   └─ Subsection A2                  A1 and A2)
```

The entire section hierarchy is transferred as a unit.

## 📁 Project Structure

```
latex-migration-tool/
├── latex_migration.py                    # Main migration script
├── migration_config_granular.json        # Example granular config
├── migration_config_hierarchical.json    # Example hierarchical config
├── example_old_for_granular.tex         # Example old template
├── example_new_with_structure.tex       # Example new template
├── run_migration.bat                     # Windows batch file (granular)
├── run_migration_hierarchical.bat       # Windows batch file (hierarchical)
└── README.md                             # This file
```

## 🔍 Examples

### Example 1: Simple Section Mapping

**Old Template:**
```latex
\section{Introduction}
This is the introduction content.
```

**New Template:**
```latex
\section{Overview}
% Content goes here
```

**Config:**
```json
{
    "mapping_mode": "granular",
    "section_mapping": {
        "Introduction": "Overview"
    }
}
```

**Result:**
```latex
\section{Overview}
This is the introduction content.
```

### Example 2: Creating New Sections

**Config:**
```json
{
    "new_sections_content": {
        "Acknowledgments": "We thank all contributors.",
        "Future Work": "We plan to extend this work."
    }
}
```

If "Acknowledgments" exists in the new template, its content is replaced.
If "Future Work" doesn't exist, a new section is created before `\end{document}`.

### Example 3: Hierarchical Mapping

Map an entire section tree from old to new template while preserving all subsections.

## 📝 Output

The tool generates:

1. **Migrated LaTeX file**: Your output file with migrated content
2. **Backup file**: Timestamped backup of the new template (`.backup.YYYYMMDD_HHMMSS`)
3. **Migration report**: Summary of the migration process (`.migration_report.txt`)

## 🐛 Troubleshooting

### Section Not Found Warning

**Issue**: `WARNING - Section 'X' not found in new template`

**Solution**: 
- Check section name spelling in config matches exactly
- Verify section exists in new template
- For new sections, add to `new_sections_content` instead

### Content Not Transferred

**Issue**: Expected content is missing in output

**Solution**:
- Use `-v` flag for verbose output
- Check migration report for details
- Verify mapping in configuration file
- Ensure correct mapping mode (granular vs. hierarchical)

### Duplicate `\end{document}`

**Issue**: Multiple `\end{document}` statements in output

**Solution**: The tool automatically removes duplicates, keeping only the last one.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

Your Name - [@yourhandle](https://twitter.com/yourhandle)

## 🙏 Acknowledgments

- Inspired by the need for flexible LaTeX template migrations
- Built for academic and professional document workflows

## 📧 Support

For questions or issues, please open an issue on GitHub or contact [your-email@example.com](mailto:your-email@example.com).

---

**Star ⭐ this repository if you find it helpful!**
