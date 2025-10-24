#!/usr/bin/env python3
"""
Abhängigkeitsanalyse und Clean Code Refactoring-Analyse für Joystick Gremlin.
Dieses Skript analysiert die Projektstruktur, erstellt ein Abhängigkeitsdiagramm
und identifiziert Clean Code Probleme.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import json


class DependencyAnalyzer:
    """Analysiert Python-Module und deren Abhängigkeiten."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.external_deps: Dict[str, Set[str]] = defaultdict(set)
        self.module_stats: Dict[str, dict] = {}
        
    def analyze_file(self, file_path: Path) -> Dict[str, any]:  # type: ignore
        """Analysiert eine Python-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
            module_name = self._get_module_name(file_path)
            
            stats = {
                'lines': len(content.splitlines()),
                'functions': 0,
                'classes': 0,
                'imports': set(),
                'external_imports': set(),
                'long_functions': [],
                'complexity_issues': []
            }
            
            # Analysiere Imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_import(module_name, alias.name, stats)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_import(module_name, node.module, stats)
                        
                elif isinstance(node, ast.FunctionDef):
                    stats['functions'] += 1
                    if node.end_lineno and node.lineno:
                        func_lines = node.end_lineno - node.lineno
                    else:
                        func_lines = 0
                    if func_lines > 50:  # Clean Code: Funktionen sollten kurz sein
                        stats['long_functions'].append({
                            'name': node.name,
                            'lines': func_lines,
                            'start': node.lineno
                        })
                        
                elif isinstance(node, ast.ClassDef):
                    stats['classes'] += 1
                    
            self.module_stats[module_name] = stats
            return stats
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}
    
    def _get_module_name(self, file_path: Path) -> str:
        """Konvertiert Dateipfad zu Modulname."""
        rel_path = file_path.relative_to(self.root_path)
        parts = list(rel_path.parts)
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace('.py', '')
        return '.'.join(parts)
    
    def _add_import(self, module_name: str, import_name: str, stats: dict):
        """Fügt einen Import hinzu und klassifiziert ihn."""
        # Interne vs externe Abhängigkeiten
        if import_name.startswith('gremlin') or import_name.startswith('linput') or import_name.startswith('action_plugins'):
            self.dependencies[module_name].add(import_name)
            stats['imports'].add(import_name)
        else:
            self.external_deps[module_name].add(import_name)
            stats['external_imports'].add(import_name)
    
    def analyze_project(self):
        """Analysiert alle Python-Dateien im Projekt."""
        for py_file in self.root_path.rglob('*.py'):
            # Skip __pycache__ und andere ignorierte Verzeichnisse
            if '__pycache__' in str(py_file) or '.bak' in str(py_file):
                continue
            self.analyze_file(py_file)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Findet zyklische Abhängigkeiten."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Zyklus gefunden
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for module in self.dependencies.keys():
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def generate_mermaid_diagram(self) -> str:
        """Generiert ein Mermaid-Diagramm der Abhängigkeiten."""
        lines = ["graph TD"]
        
        # Gruppiere Module nach Paket
        packages = defaultdict(list)
        for module in self.dependencies.keys():
            package = module.split('.')[0]
            packages[package].append(module)
        
        # Erstelle Knoten und Kanten
        for module, deps in sorted(self.dependencies.items()):
            module_short = module.split('.')[-1] if '.' in module else module
            
            for dep in sorted(deps):
                dep_short = dep.split('.')[-1] if '.' in dep else dep
                
                # Verwende unterschiedliche Farben für verschiedene Pakete
                if dep.startswith('gremlin'):
                    lines.append(f'    {module_short}[{module_short}] --> {dep_short}[{dep_short}]')
                elif dep.startswith('linput'):
                    lines.append(f'    {module_short}[{module_short}] -.->|Linux| {dep_short}[{dep_short}]')
        
        # Markiere wichtige externe Abhängigkeiten
        lines.append("\n    %% Externe Abhängigkeiten")
        external_summary = set()
        for module, ext_deps in self.external_deps.items():
            for ext in ext_deps:
                if ext in ['PySide6', 'evdev', 'pyudev', 'pynput', 'dill', 'vjoy']:
                    external_summary.add(ext)
        
        for ext in sorted(external_summary):
            lines.append(f'    {ext}{{{{"{ext}"}}}}')
        
        # Styling
        lines.append("\n    classDef gremlinClass fill:#90EE90,stroke:#333,stroke-width:2px")
        lines.append("    classDef linputClass fill:#87CEEB,stroke:#333,stroke-width:2px")
        lines.append("    classDef externalClass fill:#FFB6C1,stroke:#333,stroke-width:2px")
        
        return '\n'.join(lines)
    
    def generate_report(self) -> str:
        """Generiert einen ausführlichen Bericht."""
        report = []
        report.append("=" * 80)
        report.append("JOYSTICK GREMLIN - ABHÄNGIGKEITSANALYSE & CLEAN CODE REFACTORING")
        report.append("=" * 80)
        report.append("")
        
        # 1. Übersicht
        report.append("## 1. PROJEKTÜBERSICHT")
        report.append(f"   Gesamtanzahl Module: {len(self.module_stats)}")
        total_lines = sum(s['lines'] for s in self.module_stats.values())
        report.append(f"   Gesamtzeilen Code: {total_lines:,}")
        total_funcs = sum(s['functions'] for s in self.module_stats.values())
        report.append(f"   Gesamtanzahl Funktionen: {total_funcs}")
        total_classes = sum(s['classes'] for s in self.module_stats.values())
        report.append(f"   Gesamtanzahl Klassen: {total_classes}")
        report.append("")
        
        # 2. Externe Abhängigkeiten
        report.append("## 2. EXTERNE ABHÄNGIGKEITEN")
        all_external = set()
        for deps in self.external_deps.values():
            all_external.update(deps)
        
        report.append("   Linux-native Bibliotheken:")
        for lib in sorted(all_external):
            if lib in ['evdev', 'pyudev', 'pynput']:
                report.append(f"   - {lib}")
        
        report.append("\n   Qt/UI Bibliotheken:")
        for lib in sorted(all_external):
            if 'PySide6' in lib or 'Qt' in lib:
                report.append(f"   - {lib}")
        
        report.append("\n   Legacy Windows-Abhängigkeiten (ENTFERNEN!):")
        for lib in sorted(all_external):
            if any(x in lib for x in ['dill', 'vjoy', 'win32', 'wintypes']):
                report.append(f"   ⚠️  - {lib}")
        report.append("")
        
        # 3. Zyklische Abhängigkeiten
        report.append("## 3. ZYKLISCHE ABHÄNGIGKEITEN (CLEAN CODE VERSTOSSE)")
        cycles = self.find_circular_dependencies()
        if cycles:
            report.append(f"   ⚠️  Gefundene zyklische Abhängigkeiten: {len(cycles)}")
            for i, cycle in enumerate(cycles[:5], 1):  # Zeige die ersten 5
                cycle_str = ' -> '.join(cycle)
                report.append(f"   {i}. {cycle_str}")
        else:
            report.append("   ✓ Keine zyklischen Abhängigkeiten gefunden!")
        report.append("")
        
        # 4. Lange Funktionen (Clean Code Verstöße)
        report.append("## 4. LANGE FUNKTIONEN (> 50 Zeilen - Clean Code Verstoß)")
        long_funcs = []
        for module, stats in self.module_stats.items():
            for func in stats.get('long_functions', []):
                long_funcs.append((module, func['name'], func['lines']))
        
        long_funcs.sort(key=lambda x: x[2], reverse=True)
        if long_funcs:
            report.append(f"   ⚠️  Gefundene lange Funktionen: {len(long_funcs)}")
            for module, func_name, lines in long_funcs[:10]:  # Top 10
                report.append(f"   - {module}.{func_name}: {lines} Zeilen")
        else:
            report.append("   ✓ Alle Funktionen sind angemessen kurz!")
        report.append("")
        
        # 5. Module mit vielen Abhängigkeiten
        report.append("## 5. HOCHGEKOPPELTE MODULE (> 10 Abhängigkeiten)")
        high_coupling = []
        for module, deps in self.dependencies.items():
            if len(deps) > 10:
                high_coupling.append((module, len(deps)))
        
        high_coupling.sort(key=lambda x: x[1], reverse=True)
        if high_coupling:
            report.append(f"   ⚠️  Module mit hoher Kopplung: {len(high_coupling)}")
            for module, count in high_coupling:
                report.append(f"   - {module}: {count} Abhängigkeiten")
        else:
            report.append("   ✓ Alle Module haben angemessene Kopplung!")
        report.append("")
        
        # 6. Große Module
        report.append("## 6. GROSSE MODULE (> 500 Zeilen)")
        large_modules = [(m, s['lines']) for m, s in self.module_stats.items() if s['lines'] > 500]
        large_modules.sort(key=lambda x: x[1], reverse=True)
        
        if large_modules:
            report.append(f"   ⚠️  Große Module: {len(large_modules)}")
            for module, lines in large_modules[:10]:
                report.append(f"   - {module}: {lines:,} Zeilen")
        else:
            report.append("   ✓ Alle Module sind angemessen groß!")
        report.append("")
        
        # 7. Refactoring-Empfehlungen
        report.append("## 7. CLEAN CODE REFACTORING-EMPFEHLUNGEN")
        report.append("")
        report.append("### 7.1 Kritische Windows-Abhängigkeiten entfernen:")
        report.append("   - gremlin.util: Entfernt dill, GUID Imports")
        report.append("   - gremlin.user_script: Entfernt dill, vjoy Imports")
        report.append("   - gremlin.device_helpers: Entfernt vjoy.VJoyProxy")
        report.append("   - gremlin.process_monitor: Komplett Windows-spezifisch (win32gui, ctypes.wintypes)")
        report.append("   - gremlin.tts: win32com.client ersetzen mit Linux TTS")
        report.append("   - gremlin.windows_event_hook: Komplett entfernen")
        report.append("")
        report.append("### 7.2 Funktionen aufteilen (Single Responsibility):")
        for module, func_name, lines in long_funcs[:5]:
            report.append(f"   - {module}.{func_name} ({lines} Zeilen) → In kleinere Funktionen aufteilen")
        report.append("")
        report.append("### 7.3 Abhängigkeiten reduzieren:")
        for module, count in high_coupling[:3]:
            report.append(f"   - {module} ({count} Deps) → Dependency Injection nutzen")
        report.append("")
        report.append("### 7.4 Große Module aufteilen:")
        for module, lines in large_modules[:3]:
            report.append(f"   - {module} ({lines:,} Zeilen) → In mehrere Module aufteilen")
        report.append("")
        
        # 8. Architektur-Verbesserungen
        report.append("## 8. ARCHITEKTUR-VERBESSERUNGEN")
        report.append("")
        report.append("### 8.1 Schichtenarchitektur einführen:")
        report.append("   ```")
        report.append("   [UI Layer - PySide6]")
        report.append("        ↓")
        report.append("   [Application Layer - gremlin.*]")
        report.append("        ↓")
        report.append("   [Domain Layer - event_handler, profile, etc.]")
        report.append("        ↓")
        report.append("   [Infrastructure Layer - linput.*]")
        report.append("   ```")
        report.append("")
        report.append("### 8.2 Dependency Inversion Principle:")
        report.append("   - Interfaces/Abstrakte Klassen für Plattform-Abhängigkeiten")
        report.append("   - LinuxInputProvider implementiert IInputProvider")
        report.append("   - VirtualOutputProvider implementiert IVirtualDevice")
        report.append("")
        report.append("### 8.3 Single Responsibility:")
        report.append("   - event_handler.py: Nur Event-Routing, keine Business Logic")
        report.append("   - sendinput.py: Nur Input-Sending, keine Event-Verarbeitung")
        report.append("   - device_manager.py: Nur Device-Enumeration")
        report.append("")
        
        report.append("=" * 80)
        
        return '\n'.join(report)


def main():
    """Hauptfunktion."""
    print("🔍 Analysiere Joystick Gremlin Projekt...")
    print()
    
    root = Path(__file__).parent
    analyzer = DependencyAnalyzer(str(root))
    analyzer.analyze_project()
    
    # Generiere Bericht
    report = analyzer.generate_report()
    print(report)
    
    # Speichere Bericht
    report_file = root / "DEPENDENCY_ANALYSIS.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        f.write("\n\n## 9. ABHÄNGIGKEITSDIAGRAMM (Mermaid)\n\n")
        f.write("```mermaid\n")
        f.write(analyzer.generate_mermaid_diagram())
        f.write("\n```\n")
    
    print()
    print(f"📄 Vollständiger Bericht gespeichert: {report_file}")
    
    # Speichere JSON für weitere Analysen
    json_file = root / "dependency_data.json"
    data = {
        'dependencies': {k: list(v) for k, v in analyzer.dependencies.items()},
        'external_deps': {k: list(v) for k, v in analyzer.external_deps.items()},
        'stats': {k: {**v, 'imports': list(v.get('imports', [])), 
                      'external_imports': list(v.get('external_imports', []))} 
                  for k, v in analyzer.module_stats.items()}
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"📊 Daten gespeichert: {json_file}")


if __name__ == '__main__':
    main()
