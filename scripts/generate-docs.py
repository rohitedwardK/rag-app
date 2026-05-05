"""
Documentation Generator for Angular Applications

This script scans an Angular codebase and generates markdown documentation
that can be indexed by the RAG system.

Usage:
    python generate-docs.py <angular-app-path> <output-docs-path>

Example:
    python generate-docs.py C:/rohit/workspace/smart_web-app/ui/src/app C:/rohit/workspace/smart_web-app/docs/auto-generated
"""

import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ComponentInfo:
    name: str
    selector: str
    file_path: str
    template_url: Optional[str] = None
    description: str = ""


@dataclass
class ServiceInfo:
    name: str
    file_path: str
    description: str = ""
    methods: list = field(default_factory=list)


@dataclass
class RouteInfo:
    path: str
    component: str
    description: str = ""


@dataclass
class ModuleInfo:
    name: str
    file_path: str
    components: list = field(default_factory=list)
    services: list = field(default_factory=list)
    description: str = ""


def extract_component_info(file_path: Path) -> Optional[ComponentInfo]:
    """Extract component information from a TypeScript file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return None

    # Find @Component decorator
    component_match = re.search(
        r'@Component\s*\(\s*\{([^}]+)\}\s*\)',
        content,
        re.DOTALL
    )
    if not component_match:
        return None

    decorator_content = component_match.group(1)

    # Extract selector
    selector_match = re.search(r"selector\s*:\s*['\"]([^'\"]+)['\"]", decorator_content)
    selector = selector_match.group(1) if selector_match else ""

    # Extract class name
    class_match = re.search(r'export\s+class\s+(\w+)', content)
    class_name = class_match.group(1) if class_match else file_path.stem

    # Extract template URL
    template_match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", decorator_content)
    template_url = template_match.group(1) if template_match else None

    # Extract JSDoc comment if present
    jsdoc_match = re.search(r'/\*\*\s*\n([^*]|\*(?!/))*\*/\s*@Component', content)
    description = ""
    if jsdoc_match:
        desc = jsdoc_match.group(0)
        desc = re.sub(r'/\*\*|\*/|@Component|\*', '', desc)
        description = ' '.join(desc.split()).strip()

    return ComponentInfo(
        name=class_name,
        selector=selector,
        file_path=str(file_path),
        template_url=template_url,
        description=description
    )


def extract_service_info(file_path: Path) -> Optional[ServiceInfo]:
    """Extract service information from a TypeScript file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return None

    # Find @Injectable decorator
    if '@Injectable' not in content:
        return None

    # Extract class name
    class_match = re.search(r'export\s+class\s+(\w+)', content)
    if not class_match:
        return None

    class_name = class_match.group(1)

    # Extract public methods
    methods = re.findall(r'(?:public\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{', content)
    methods = [m for m in methods if not m.startswith('_') and m not in ['constructor', 'ngOnInit', 'ngOnDestroy']]

    return ServiceInfo(
        name=class_name,
        file_path=str(file_path),
        methods=methods[:10]  # Limit to first 10 methods
    )


def extract_routes(routing_file: Path) -> list[RouteInfo]:
    """Extract route information from a routing module."""
    try:
        content = routing_file.read_text(encoding='utf-8')
    except Exception:
        return []

    routes = []
    # Match route definitions
    route_matches = re.findall(
        r"\{\s*path\s*:\s*['\"]([^'\"]+)['\"][^}]*component\s*:\s*(\w+)",
        content,
        re.DOTALL
    )

    for path, component in route_matches:
        routes.append(RouteInfo(path=path, component=component))

    return routes


def extract_module_info(file_path: Path) -> Optional[ModuleInfo]:
    """Extract module information from a module file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return None

    if '@NgModule' not in content:
        return None

    # Extract class name
    class_match = re.search(r'export\s+class\s+(\w+)', content)
    if not class_match:
        return None

    # Extract declarations
    declarations_match = re.search(r'declarations\s*:\s*\[([^\]]+)\]', content, re.DOTALL)
    components = []
    if declarations_match:
        decl_content = declarations_match.group(1)
        components = re.findall(r'(\w+Component)', decl_content)

    return ModuleInfo(
        name=class_match.group(1),
        file_path=str(file_path),
        components=components
    )


def scan_angular_app(app_path: Path) -> dict:
    """Scan an Angular application and extract all information."""
    result = {
        'modules': [],
        'components': [],
        'services': [],
        'routes': []
    }

    # Find all TypeScript files
    for ts_file in app_path.rglob('*.ts'):
        # Skip test files and node_modules
        if '.spec.' in ts_file.name or 'node_modules' in str(ts_file):
            continue

        file_name = ts_file.name

        if file_name.endswith('.module.ts'):
            module_info = extract_module_info(ts_file)
            if module_info:
                result['modules'].append(module_info)

        elif file_name.endswith('.component.ts'):
            comp_info = extract_component_info(ts_file)
            if comp_info:
                result['components'].append(comp_info)

        elif file_name.endswith('.service.ts'):
            service_info = extract_service_info(ts_file)
            if service_info:
                result['services'].append(service_info)

        elif 'routing' in file_name.lower():
            routes = extract_routes(ts_file)
            result['routes'].extend(routes)

    return result


def infer_feature_from_path(file_path: str, app_path: str) -> str:
    """Infer the feature name from the file path."""
    rel_path = file_path.replace(app_path, '').replace('\\', '/')
    parts = [p for p in rel_path.split('/') if p and p != 'src' and p != 'app']
    if parts:
        return parts[0].replace('-', ' ').title()
    return 'Core'


def generate_overview_doc(app_info: dict, app_name: str) -> str:
    """Generate an overview documentation file."""
    doc = f"""# {app_name} Application Overview

## Summary

This documentation is auto-generated from the application source code.

- **Total Modules**: {len(app_info['modules'])}
- **Total Components**: {len(app_info['components'])}
- **Total Services**: {len(app_info['services'])}
- **Total Routes**: {len(app_info['routes'])}

## Available Routes

| Path | Component | Description |
|------|-----------|-------------|
"""
    for route in app_info['routes']:
        doc += f"| `/{route.path}` | {route.component} | {route.description} |\n"

    doc += """
## Feature Modules

"""
    for module in app_info['modules']:
        feature = infer_feature_from_path(module.file_path, '')
        doc += f"- **{module.name}** ({feature}): {len(module.components)} components\n"

    return doc


def generate_feature_doc(feature_name: str, components: list, services: list, routes: list) -> str:
    """Generate documentation for a feature."""
    doc = f"""# {feature_name}

## Overview

This document describes the {feature_name} feature of the application.

## Components

"""
    if components:
        for comp in components:
            doc += f"""### {comp.name}

- **Selector**: `{comp.selector}`
- **Description**: {comp.description or 'Component for ' + feature_name.lower() + ' functionality'}

"""
    else:
        doc += "No components found for this feature.\n\n"

    doc += "## Services\n\n"
    if services:
        for svc in services:
            doc += f"""### {svc.name}

Service providing business logic for {feature_name.lower()}.

**Available Methods**:
"""
            for method in svc.methods[:5]:
                doc += f"- `{method}()`\n"
            doc += "\n"
    else:
        doc += "No dedicated services for this feature.\n\n"

    doc += "## Routes\n\n"
    if routes:
        for route in routes:
            doc += f"- **/{route.path}** → {route.component}\n"
    else:
        doc += "No dedicated routes for this feature.\n"

    return doc


def group_by_feature(app_info: dict, app_path: str) -> dict:
    """Group components and services by feature."""
    features = {}

    for comp in app_info['components']:
        feature = infer_feature_from_path(comp.file_path, app_path)
        if feature not in features:
            features[feature] = {'components': [], 'services': [], 'routes': []}
        features[feature]['components'].append(comp)

    for svc in app_info['services']:
        feature = infer_feature_from_path(svc.file_path, app_path)
        if feature not in features:
            features[feature] = {'components': [], 'services': [], 'routes': []}
        features[feature]['services'].append(svc)

    # Try to match routes to features
    for route in app_info['routes']:
        matched = False
        for feature_name, feature_data in features.items():
            for comp in feature_data['components']:
                if comp.name == route.component:
                    feature_data['routes'].append(route)
                    matched = True
                    break
            if matched:
                break

    return features


def generate_docs(app_path: str, output_path: str, app_name: str = "Application"):
    """Main function to generate documentation."""
    app_path = Path(app_path).resolve()
    output_path = Path(output_path).resolve()

    print(f"Scanning Angular app at: {app_path}")

    # Scan the application
    app_info = scan_angular_app(app_path)

    print(f"Found: {len(app_info['modules'])} modules, {len(app_info['components'])} components, "
          f"{len(app_info['services'])} services, {len(app_info['routes'])} routes")

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate overview doc
    overview = generate_overview_doc(app_info, app_name)
    (output_path / 'overview.md').write_text(overview, encoding='utf-8')
    print(f"Generated: overview.md")

    # Group by feature and generate feature docs
    features = group_by_feature(app_info, str(app_path))

    features_dir = output_path / 'features'
    features_dir.mkdir(exist_ok=True)

    for feature_name, feature_data in features.items():
        if not feature_data['components'] and not feature_data['services']:
            continue

        doc = generate_feature_doc(
            feature_name,
            feature_data['components'],
            feature_data['services'],
            feature_data['routes']
        )

        file_name = feature_name.lower().replace(' ', '-') + '.md'
        (features_dir / file_name).write_text(doc, encoding='utf-8')
        print(f"Generated: features/{file_name}")

    print(f"\nDocumentation generated at: {output_path}")
    return len(features) + 1  # +1 for overview


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate documentation from Angular codebase')
    parser.add_argument('app_path', help='Path to Angular app source (e.g., ui/src/app)')
    parser.add_argument('output_path', help='Path to output documentation folder')
    parser.add_argument('--name', default='Application', help='Application name for docs')

    args = parser.parse_args()

    generate_docs(args.app_path, args.output_path, args.name)
