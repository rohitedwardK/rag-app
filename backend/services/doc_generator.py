"""
Documentation Generator Service

Scans an Angular codebase and generates markdown documentation for RAG indexing.
Extracts JSDoc comments, method signatures, decorators, inputs/outputs, and dependencies.
"""

import os
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class MethodInfo:
    """Information about a class method."""
    name: str
    signature: str
    return_type: str = ""
    description: str = ""
    params: List[Dict[str, str]] = field(default_factory=list)
    is_async: bool = False
    visibility: str = "public"


@dataclass
class PropertyInfo:
    """Information about a class property or @Input/@Output."""
    name: str
    type: str = ""
    default_value: str = ""
    description: str = ""
    decorator: str = ""  # 'Input', 'Output', 'ViewChild', etc.


@dataclass
class ComponentInfo:
    name: str
    selector: str
    file_path: str
    template_url: Optional[str] = None
    style_urls: List[str] = field(default_factory=list)
    description: str = ""
    inputs: List[PropertyInfo] = field(default_factory=list)
    outputs: List[PropertyInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    extends: str = ""


@dataclass
class ServiceInfo:
    name: str
    file_path: str
    description: str = ""
    methods: List[MethodInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    provided_in: str = ""


@dataclass
class RouteInfo:
    path: str
    component: str
    description: str = ""
    guards: List[str] = field(default_factory=list)
    children: List['RouteInfo'] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleInfo:
    name: str
    file_path: str
    components: list = field(default_factory=list)
    services: list = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    description: str = ""


class DocGeneratorService:
    """Service to generate documentation from Angular codebases."""

    def _extract_jsdoc(self, content: str, before_pattern: str) -> Dict[str, Any]:
        """
        Extract JSDoc comment before a pattern (e.g., @Component, method definition).
        Returns dict with: description, params, returns, example, etc.
        """
        result = {
            'description': '',
            'params': [],
            'returns': '',
            'example': '',
            'deprecated': False,
            'see': [],
            'tags': {}
        }
        
        jsdoc_pattern = rf'/\*\*\s*([\s\S]*?)\*/\s*(?={re.escape(before_pattern)[:20]})'
        match = re.search(jsdoc_pattern, content)
        if not match:
            return result
        
        jsdoc_content = match.group(1)
        lines = [line.strip().lstrip('*').strip() for line in jsdoc_content.split('\n')]
        
        current_tag = None
        description_lines = []
        
        for line in lines:
            if line.startswith('@param'):
                param_match = re.match(r'@param\s+(?:\{([^}]+)\})?\s*(\w+)\s*(.*)', line)
                if param_match:
                    result['params'].append({
                        'type': param_match.group(1) or '',
                        'name': param_match.group(2),
                        'description': param_match.group(3)
                    })
            elif line.startswith('@returns') or line.startswith('@return'):
                returns_match = re.match(r'@returns?\s+(?:\{([^}]+)\})?\s*(.*)', line)
                if returns_match:
                    result['returns'] = returns_match.group(2) or returns_match.group(1) or ''
            elif line.startswith('@example'):
                current_tag = 'example'
            elif line.startswith('@deprecated'):
                result['deprecated'] = True
                result['tags']['deprecated'] = line.replace('@deprecated', '').strip()
            elif line.startswith('@see'):
                result['see'].append(line.replace('@see', '').strip())
            elif line.startswith('@'):
                tag_match = re.match(r'@(\w+)\s*(.*)', line)
                if tag_match:
                    result['tags'][tag_match.group(1)] = tag_match.group(2)
            elif current_tag == 'example':
                result['example'] += line + '\n'
            else:
                description_lines.append(line)
        
        result['description'] = ' '.join(description_lines).strip()
        return result

    def _extract_method_info(self, content: str) -> List[MethodInfo]:
        """Extract detailed method information including signatures and JSDoc."""
        methods = []
        
        method_pattern = r'''
            (?:/\*\*[\s\S]*?\*/\s*)?  # Optional JSDoc
            (?:(async)\s+)?          # Optional async
            (?:(public|private|protected)\s+)?  # Optional visibility
            (\w+)\s*                  # Method name
            (<[^>]+>)?               # Optional generics
            \(([^)]*)\)              # Parameters
            \s*(?::\s*([^{;]+))?     # Optional return type
            \s*\{                    # Method body start
        '''
        
        for match in re.finditer(method_pattern, content, re.VERBOSE):
            is_async = match.group(1) is not None
            visibility = match.group(2) or 'public'
            method_name = match.group(3)
            generics = match.group(4) or ''
            params_str = match.group(5)
            return_type = (match.group(6) or '').strip()
            
            if method_name in ['constructor', 'ngOnInit', 'ngOnDestroy', 'ngOnChanges', 
                              'ngAfterViewInit', 'ngAfterContentInit', 'if', 'for', 'while', 'switch']:
                continue
            
            if method_name.startswith('_'):
                continue
                
            method_start = match.start()
            jsdoc_info = self._extract_jsdoc(content[:method_start + 50], method_name)
            
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        param_parts = param.split(':')
                        param_name = param_parts[0].strip().lstrip('?')
                        param_type = param_parts[1].strip() if len(param_parts) > 1 else ''
                        param_desc = ''
                        for p in jsdoc_info['params']:
                            if p['name'] == param_name:
                                param_desc = p['description']
                                if not param_type:
                                    param_type = p['type']
                                break
                        params.append({'name': param_name, 'type': param_type, 'description': param_desc})
            
            signature = f"{method_name}{generics}({params_str})"
            if return_type:
                signature += f": {return_type}"
            
            methods.append(MethodInfo(
                name=method_name,
                signature=signature,
                return_type=return_type,
                description=jsdoc_info['description'],
                params=params,
                is_async=is_async,
                visibility=visibility
            ))
        
        return methods[:20]

    def _extract_inputs_outputs(self, content: str) -> tuple[List[PropertyInfo], List[PropertyInfo]]:
        """Extract @Input() and @Output() decorators with their types and descriptions."""
        inputs = []
        outputs = []
        
        input_pattern = r'''
            (?:/\*\*[\s\S]*?\*/\s*)?  # Optional JSDoc
            @Input\s*\(([^)]*)\)\s*   # @Input decorator with optional config
            (\w+)\s*                   # Property name
            (?::\s*([^=;]+))?         # Optional type
            (?:\s*=\s*([^;]+))?       # Optional default value
        '''
        
        for match in re.finditer(input_pattern, content, re.VERBOSE):
            prop_start = match.start()
            jsdoc_info = self._extract_jsdoc(content[:prop_start + 30], '@Input')
            
            input_config = match.group(1).strip() if match.group(1) else ''
            prop_name = match.group(2)
            prop_type = (match.group(3) or '').strip().rstrip(',')
            default_value = (match.group(4) or '').strip().rstrip(';')
            
            alias = ''
            if input_config:
                alias_match = re.search(r"['\"](\w+)['\"]", input_config)
                if alias_match:
                    alias = alias_match.group(1)
            
            inputs.append(PropertyInfo(
                name=prop_name,
                type=prop_type,
                default_value=default_value,
                description=jsdoc_info['description'] or (f"Alias: {alias}" if alias else ''),
                decorator='Input'
            ))
        
        output_pattern = r'''
            (?:/\*\*[\s\S]*?\*/\s*)?  # Optional JSDoc
            @Output\s*\(([^)]*)\)\s*  # @Output decorator
            (\w+)\s*                   # Property name
            (?::\s*([^=;]+))?         # Optional type
            (?:\s*=\s*([^;]+))?       # Optional initializer
        '''
        
        for match in re.finditer(output_pattern, content, re.VERBOSE):
            prop_start = match.start()
            jsdoc_info = self._extract_jsdoc(content[:prop_start + 30], '@Output')
            
            prop_name = match.group(2)
            prop_type = (match.group(3) or '').strip().rstrip(',')
            
            outputs.append(PropertyInfo(
                name=prop_name,
                type=prop_type,
                description=jsdoc_info['description'],
                decorator='Output'
            ))
        
        return inputs, outputs

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract constructor dependencies (injected services)."""
        dependencies = []
        
        constructor_match = re.search(
            r'constructor\s*\(([^)]*)\)',
            content,
            re.DOTALL
        )
        
        if constructor_match:
            params_str = constructor_match.group(1)
            param_pattern = r'(?:private|public|protected|readonly)?\s*(\w+)\s*:\s*(\w+)'
            for match in re.finditer(param_pattern, params_str):
                dep_type = match.group(2)
                if dep_type and dep_type[0].isupper():
                    dependencies.append(dep_type)
        
        return dependencies

    def _extract_class_hierarchy(self, content: str) -> tuple[str, List[str]]:
        """Extract extends and implements from class declaration."""
        extends = ""
        implements = []
        
        class_match = re.search(
            r'export\s+class\s+\w+(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?',
            content
        )
        
        if class_match:
            extends = class_match.group(1) or ""
            if class_match.group(2):
                implements = [i.strip() for i in class_match.group(2).split(',')]
        
        return extends, implements

    def extract_component_info(self, file_path: Path) -> Optional[ComponentInfo]:
        """Extract comprehensive component information from a TypeScript file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        component_match = re.search(
            r'@Component\s*\(\s*\{([\s\S]*?)\}\s*\)',
            content
        )
        if not component_match:
            return None

        decorator_content = component_match.group(1)

        selector_match = re.search(r"selector\s*:\s*['\"]([^'\"]+)['\"]", decorator_content)
        selector = selector_match.group(1) if selector_match else ""

        class_match = re.search(r'export\s+class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else file_path.stem

        template_match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", decorator_content)
        template_url = template_match.group(1) if template_match else None

        style_urls = []
        styles_match = re.search(r"styleUrls?\s*:\s*\[([^\]]+)\]", decorator_content)
        if styles_match:
            style_urls = re.findall(r"['\"]([^'\"]+)['\"]", styles_match.group(1))

        jsdoc_info = self._extract_jsdoc(content, '@Component')
        inputs, outputs = self._extract_inputs_outputs(content)
        methods = self._extract_method_info(content)
        dependencies = self._extract_dependencies(content)
        extends, implements = self._extract_class_hierarchy(content)

        return ComponentInfo(
            name=class_name,
            selector=selector,
            file_path=str(file_path),
            template_url=template_url,
            style_urls=style_urls,
            description=jsdoc_info['description'],
            inputs=inputs,
            outputs=outputs,
            methods=methods,
            dependencies=dependencies,
            extends=extends,
            implements=implements
        )

    def extract_service_info(self, file_path: Path) -> Optional[ServiceInfo]:
        """Extract comprehensive service information from a TypeScript file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        if '@Injectable' not in content:
            return None

        class_match = re.search(r'export\s+class\s+(\w+)', content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        provided_in = ""
        injectable_match = re.search(r"@Injectable\s*\(\s*\{([^}]*)\}", content)
        if injectable_match:
            provided_match = re.search(r"providedIn\s*:\s*['\"]([^'\"]+)['\"]", injectable_match.group(1))
            if provided_match:
                provided_in = provided_match.group(1)

        jsdoc_info = self._extract_jsdoc(content, '@Injectable')
        methods = self._extract_method_info(content)
        dependencies = self._extract_dependencies(content)

        return ServiceInfo(
            name=class_name,
            file_path=str(file_path),
            description=jsdoc_info['description'],
            methods=methods,
            dependencies=dependencies,
            provided_in=provided_in
        )

    def extract_routes(self, routing_file: Path) -> List[RouteInfo]:
        """Extract detailed route information from a routing module."""
        try:
            content = routing_file.read_text(encoding='utf-8')
        except Exception:
            return []

        routes = []
        
        route_pattern = r'''
            \{\s*
            path\s*:\s*['\"]([^'\"]*)['\"]  # Path (can be empty string)
            ([^}]*?)                          # Rest of route config
            \}
        '''
        
        for match in re.finditer(route_pattern, content, re.VERBOSE | re.DOTALL):
            path = match.group(1)
            route_config = match.group(2)
            
            component_match = re.search(r'component\s*:\s*(\w+)', route_config)
            component = component_match.group(1) if component_match else ''
            
            guards = []
            guard_types = ['canActivate', 'canDeactivate', 'canLoad', 'canMatch']
            for guard_type in guard_types:
                guard_match = re.search(rf'{guard_type}\s*:\s*\[([^\]]+)\]', route_config)
                if guard_match:
                    found_guards = re.findall(r'(\w+)', guard_match.group(1))
                    guards.extend(found_guards)
            
            data = {}
            data_match = re.search(r'data\s*:\s*\{([^}]+)\}', route_config)
            if data_match:
                data_content = data_match.group(1)
                title_match = re.search(r"title\s*:\s*['\"]([^'\"]+)['\"]", data_content)
                if title_match:
                    data['title'] = title_match.group(1)
                roles_match = re.search(r'roles\s*:\s*\[([^\]]+)\]', data_content)
                if roles_match:
                    data['roles'] = re.findall(r"['\"]([^'\"]+)['\"]", roles_match.group(1))
            
            if path or component:
                routes.append(RouteInfo(
                    path=path,
                    component=component,
                    guards=guards,
                    data=data
                ))

        return routes

    def extract_module_info(self, file_path: Path) -> Optional[ModuleInfo]:
        """Extract comprehensive module information from a module file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        if '@NgModule' not in content:
            return None

        class_match = re.search(r'export\s+class\s+(\w+)', content)
        if not class_match:
            return None

        jsdoc_info = self._extract_jsdoc(content, '@NgModule')

        declarations_match = re.search(r'declarations\s*:\s*\[([^\]]+)\]', content, re.DOTALL)
        components = []
        if declarations_match:
            decl_content = declarations_match.group(1)
            components = re.findall(r'(\w+(?:Component|Directive|Pipe))', decl_content)

        imports_match = re.search(r'imports\s*:\s*\[([^\]]+)\]', content, re.DOTALL)
        imports = []
        if imports_match:
            imports_content = imports_match.group(1)
            imports = re.findall(r'(\w+Module)', imports_content)

        exports_match = re.search(r'exports\s*:\s*\[([^\]]+)\]', content, re.DOTALL)
        exports = []
        if exports_match:
            exports_content = exports_match.group(1)
            exports = re.findall(r'(\w+(?:Component|Directive|Pipe|Module))', exports_content)

        providers_match = re.search(r'providers\s*:\s*\[([^\]]+)\]', content, re.DOTALL)
        providers = []
        if providers_match:
            providers_content = providers_match.group(1)
            providers = re.findall(r'(\w+Service|\w+Guard|\w+Interceptor)', providers_content)

        return ModuleInfo(
            name=class_match.group(1),
            file_path=str(file_path),
            components=components,
            imports=imports,
            exports=exports,
            providers=providers,
            description=jsdoc_info['description']
        )

    def scan_angular_app(self, app_path: Path) -> dict:
        """Scan an Angular application and extract all information."""
        result = {
            'modules': [],
            'components': [],
            'services': [],
            'routes': []
        }

        for ts_file in app_path.rglob('*.ts'):
            if '.spec.' in ts_file.name or 'node_modules' in str(ts_file):
                continue

            file_name = ts_file.name

            if file_name.endswith('.module.ts'):
                module_info = self.extract_module_info(ts_file)
                if module_info:
                    result['modules'].append(module_info)

            elif file_name.endswith('.component.ts'):
                comp_info = self.extract_component_info(ts_file)
                if comp_info:
                    result['components'].append(comp_info)

            elif file_name.endswith('.service.ts'):
                service_info = self.extract_service_info(ts_file)
                if service_info:
                    result['services'].append(service_info)

            elif 'routing' in file_name.lower():
                routes = self.extract_routes(ts_file)
                result['routes'].extend(routes)

        return result

    def infer_feature_from_path(self, file_path: str, app_path: str) -> str:
        """Infer the feature name from the file path."""
        rel_path = file_path.replace(app_path, '').replace('\\', '/')
        parts = [p for p in rel_path.split('/') if p and p != 'src' and p != 'app']
        if parts:
            return parts[0].replace('-', ' ').title()
        return 'Core'

    def generate_overview_doc(self, app_info: dict, app_name: str) -> str:
        """Generate an overview documentation file."""
        doc = f"""# {app_name} Application Overview

## Summary

This documentation is auto-generated from the application source code.
It provides comprehensive information about components, services, routes, and their relationships.

### Statistics

- **Total Modules**: {len(app_info['modules'])}
- **Total Components**: {len(app_info['components'])}
- **Total Services**: {len(app_info['services'])}
- **Total Routes**: {len(app_info['routes'])}

## Application Routes

| Path | Component | Guards | Data |
|------|-----------|--------|------|
"""
        for route in app_info['routes']:
            guards_str = ', '.join(route.guards) if route.guards else '-'
            data_str = ', '.join(f"{k}={v}" for k, v in route.data.items()) if route.data else '-'
            doc += f"| `/{route.path}` | {route.component} | {guards_str} | {data_str} |\n"

        doc += """
## Feature Modules

"""
        for module in app_info['modules']:
            feature = self.infer_feature_from_path(module.file_path, '')
            imports_count = len(module.imports) if hasattr(module, 'imports') else 0
            providers_count = len(module.providers) if hasattr(module, 'providers') else 0
            desc = f" - {module.description}" if module.description else ""
            doc += f"- **{module.name}** ({feature}): {len(module.components)} declarations, {imports_count} imports, {providers_count} providers{desc}\n"

        doc += """
## Services Overview

"""
        for service in app_info['services']:
            method_count = len(service.methods) if service.methods else 0
            deps_str = f" (depends on: {', '.join(service.dependencies)})" if service.dependencies else ""
            doc += f"- **{service.name}**: {method_count} public methods{deps_str}\n"

        return doc

    def generate_feature_doc(self, feature_name: str, components: list, services: list, routes: list) -> str:
        """Generate comprehensive documentation for a feature."""
        doc = f"""# {feature_name}

## Overview

This document describes the {feature_name} feature of the application.

## Components

"""
        if components:
            for comp in components:
                doc += f"""### {comp.name}

- **Selector**: `<{comp.selector}>`
- **File**: `{comp.file_path.split('/')[-1] if '/' in comp.file_path else comp.file_path.split(chr(92))[-1]}`
"""
                if comp.description:
                    doc += f"- **Description**: {comp.description}\n"
                
                if comp.extends:
                    doc += f"- **Extends**: `{comp.extends}`\n"
                
                if comp.implements:
                    doc += f"- **Implements**: {', '.join(f'`{i}`' for i in comp.implements)}\n"
                
                if comp.dependencies:
                    doc += f"- **Dependencies**: {', '.join(f'`{d}`' for d in comp.dependencies)}\n"
                
                if comp.inputs:
                    doc += "\n#### Inputs\n\n"
                    doc += "| Name | Type | Default | Description |\n"
                    doc += "|------|------|---------|-------------|\n"
                    for inp in comp.inputs:
                        default = inp.default_value or '-'
                        type_str = f"`{inp.type}`" if inp.type else '-'
                        desc = inp.description or '-'
                        doc += f"| `{inp.name}` | {type_str} | {default} | {desc} |\n"
                
                if comp.outputs:
                    doc += "\n#### Outputs (Events)\n\n"
                    doc += "| Name | Type | Description |\n"
                    doc += "|------|------|-------------|\n"
                    for out in comp.outputs:
                        type_str = f"`{out.type}`" if out.type else '-'
                        desc = out.description or '-'
                        doc += f"| `{out.name}` | {type_str} | {desc} |\n"
                
                if comp.methods:
                    doc += "\n#### Public Methods\n\n"
                    for method in comp.methods[:10]:
                        async_str = "async " if method.is_async else ""
                        doc += f"##### `{async_str}{method.signature}`\n\n"
                        if method.description:
                            doc += f"{method.description}\n\n"
                        if method.params:
                            doc += "**Parameters:**\n"
                            for param in method.params:
                                type_str = f" (`{param['type']}`)" if param.get('type') else ""
                                desc = f" - {param['description']}" if param.get('description') else ""
                                doc += f"- `{param['name']}`{type_str}{desc}\n"
                            doc += "\n"
                        if method.return_type:
                            doc += f"**Returns:** `{method.return_type}`\n\n"
                
                doc += "\n---\n\n"
        else:
            doc += "No components found for this feature.\n\n"

        doc += "## Services\n\n"
        if services:
            for svc in services:
                doc += f"""### {svc.name}

"""
                if svc.description:
                    doc += f"{svc.description}\n\n"
                else:
                    doc += f"Service providing business logic for {feature_name.lower()}.\n\n"
                
                if svc.provided_in:
                    doc += f"- **Provided In**: `{svc.provided_in}`\n"
                
                if svc.dependencies:
                    doc += f"- **Dependencies**: {', '.join(f'`{d}`' for d in svc.dependencies)}\n"
                
                if svc.methods:
                    doc += "\n#### Methods\n\n"
                    for method in svc.methods[:15]:
                        async_str = "async " if method.is_async else ""
                        doc += f"##### `{async_str}{method.signature}`\n\n"
                        if method.description:
                            doc += f"{method.description}\n\n"
                        if method.params:
                            doc += "**Parameters:**\n"
                            for param in method.params:
                                type_str = f" (`{param['type']}`)" if param.get('type') else ""
                                desc = f" - {param['description']}" if param.get('description') else ""
                                doc += f"- `{param['name']}`{type_str}{desc}\n"
                            doc += "\n"
                        if method.return_type:
                            doc += f"**Returns:** `{method.return_type}`\n\n"
                
                doc += "\n---\n\n"
        else:
            doc += "No dedicated services for this feature.\n\n"

        doc += "## Routes\n\n"
        if routes:
            doc += "| Path | Component | Guards |\n"
            doc += "|------|-----------|--------|\n"
            for route in routes:
                guards_str = ', '.join(route.guards) if route.guards else '-'
                doc += f"| `/{route.path}` | `{route.component}` | {guards_str} |\n"
        else:
            doc += "No dedicated routes for this feature.\n"

        return doc

    def group_by_feature(self, app_info: dict, app_path: str) -> dict:
        """Group components and services by feature."""
        features = {}

        for comp in app_info['components']:
            feature = self.infer_feature_from_path(comp.file_path, app_path)
            if feature not in features:
                features[feature] = {'components': [], 'services': [], 'routes': []}
            features[feature]['components'].append(comp)

        for svc in app_info['services']:
            feature = self.infer_feature_from_path(svc.file_path, app_path)
            if feature not in features:
                features[feature] = {'components': [], 'services': [], 'routes': []}
            features[feature]['services'].append(svc)

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

    def generate_docs(self, app_path: str, output_path: str, app_name: str = "Application") -> dict:
        """Main function to generate documentation."""
        app_path_obj = Path(app_path).resolve()
        output_path_obj = Path(output_path).resolve()

        logger.info(f"Scanning Angular app at: {app_path_obj}")

        app_info = self.scan_angular_app(app_path_obj)

        logger.info(f"Found: {len(app_info['modules'])} modules, {len(app_info['components'])} components, "
                    f"{len(app_info['services'])} services, {len(app_info['routes'])} routes")

        output_path_obj.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Generate overview doc
        overview = self.generate_overview_doc(app_info, app_name)
        overview_file = output_path_obj / 'overview.md'
        overview_file.write_text(overview, encoding='utf-8')
        generated_files.append(str(overview_file))
        logger.info("Generated: overview.md")

        # Group by feature and generate feature docs
        features = self.group_by_feature(app_info, str(app_path_obj))

        features_dir = output_path_obj / 'features'
        features_dir.mkdir(exist_ok=True)

        for feature_name, feature_data in features.items():
            if not feature_data['components'] and not feature_data['services']:
                continue

            doc = self.generate_feature_doc(
                feature_name,
                feature_data['components'],
                feature_data['services'],
                feature_data['routes']
            )

            file_name = feature_name.lower().replace(' ', '-') + '.md'
            feature_file = features_dir / file_name
            feature_file.write_text(doc, encoding='utf-8')
            generated_files.append(str(feature_file))
            logger.info(f"Generated: features/{file_name}")

        return {
            'output_path': str(output_path_obj),
            'files_generated': len(generated_files),
            'files': generated_files,
            'stats': {
                'modules': len(app_info['modules']),
                'components': len(app_info['components']),
                'services': len(app_info['services']),
                'routes': len(app_info['routes']),
                'features': len(features)
            }
        }
