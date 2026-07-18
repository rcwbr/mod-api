"""Unit tests for EffectsRegistry - LV2 plugin discovery and parsing."""

import pytest
from unittest.mock import MagicMock, patch

from mod_api.models import Port


class TestEffectsRegistryInit:
    """Tests for EffectsRegistry initialization."""

    def test_registry_initializes_empty(self):
        """Test registry starts with empty effects catalog."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()
        assert registry._effects == {}
        assert registry.get_all() == []

    def test_get_nonexistent_effect_returns_none(self):
        """Test getting nonexistent effect returns None."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()
        result = registry.get("http://nonexistent/effect")
        assert result is None


class TestEffectsRegistryGet:
    """Tests for EffectsRegistry.get method."""

    def test_get_returns_effect_info(self):
        """Test getting an effect by URI returns EffectInfo."""
        from mod_api.effects.registry import EffectsRegistry, EffectInfo
        from mod_api.models import NumberParameterType

        registry = EffectsRegistry()
        effect_info = EffectInfo(
            uri="http://test/plugin",
            name="Test Plugin",
            ports=[Port(name="input", type="input")],
            parameters={
                "gain": NumberParameterType(name="gain", min=0.0, max=1.0, default=0.5)
            }
        )
        registry._effects["http://test/plugin"] = effect_info

        result = registry.get("http://test/plugin")
        assert result is not None
        assert result.uri == "http://test/plugin"
        assert result.name == "Test Plugin"

    def test_get_all_returns_all_effects(self):
        """Test get_all returns all discovered effects."""
        from mod_api.effects.registry import EffectsRegistry, EffectInfo

        registry = EffectsRegistry()
        effect1 = EffectInfo(
            uri="http://test/plugin1",
            name="Plugin 1",
            ports=[],
            parameters={}
        )
        effect2 = EffectInfo(
            uri="http://test/plugin2",
            name="Plugin 2",
            ports=[],
            parameters={}
        )
        registry._effects = {
            "http://test/plugin1": effect1,
            "http://test/plugin2": effect2
        }

        result = registry.get_all()
        assert len(result) == 2
        uris = {e.uri for e in result}
        assert "http://test/plugin1" in uris
        assert "http://test/plugin2" in uris


class TestEffectsRegistryDiscover:
    """Tests for EffectsRegistry.discover method."""

    @patch('mod_api.effects.registry.EffectsRegistry._scan_lv2_path')
    def test_discover_clears_existing_effects(self, mock_scan):
        """Test discover clears any existing effects before scanning."""
        from mod_api.effects.registry import EffectsRegistry, EffectInfo

        registry = EffectsRegistry()
        registry._effects["http://old/effect"] = EffectInfo(
            uri="http://old/effect",
            name="Old",
            ports=[],
            parameters={}
        )
        mock_scan.return_value = []

        registry.discover()
        assert registry._effects == {}

    @patch('mod_api.effects.registry.EffectsRegistry._scan_lv2_path')
    def test_discover_returns_discovered_effects(self, mock_scan):
        """Test discover returns list of EffectInfo objects."""
        from mod_api.effects.registry import EffectsRegistry, EffectInfo

        registry = EffectsRegistry()
        mock_scan.return_value = []

        result = registry.discover()
        assert isinstance(result, list)


class TestParsePortNode:
    """Tests for _parse_port_node method."""

    def test_parse_audio_input_port(self):
        """Test parsing an audio input port."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        registry = EffectsRegistry()

        # Create a mock graph
        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/port1")
        graph.add((port_node, LV2.symbol, Literal("input")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#AudioPort")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#InputPort")))

        result = registry._parse_port_node(graph, port_node)
        assert result is not None
        assert result["name"] == "input"
        assert result["type"] == "input"

    def test_parse_audio_output_port(self):
        """Test parsing an audio output port."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        registry = EffectsRegistry()

        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/port2")
        graph.add((port_node, LV2.symbol, Literal("output")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#AudioPort")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#OutputPort")))

        result = registry._parse_port_node(graph, port_node)
        assert result is not None
        assert result["name"] == "output"
        assert result["type"] == "output"

    def test_parse_parameter_port(self):
        """Test parsing a control port as parameter."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        registry = EffectsRegistry()

        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/port3")
        graph.add((port_node, LV2.symbol, Literal("drive")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#ControlPort")))

        result = registry._parse_port_node(graph, port_node)
        assert result is not None
        assert result["name"] == "drive"
        assert result["type"] == "parameter"
        assert result["parameter"] is not None


class TestCreateParameterFromPort:
    """Tests for _create_parameter_from_port method."""

    def test_numeric_parameter_default_range(self):
        """Test numeric parameter with default range."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, URIRef, Literal

        registry = EffectsRegistry()
        graph = Graph()

        port_node = URIRef("http://test/param1")
        result = registry._create_parameter_from_port(graph, port_node, "test_param")

        assert result.name == "test_param"
        assert result.type == "number"
        assert result.min == 0.0
        assert result.max == 1.0
        assert result.default == 0.5

    def test_numeric_parameter_with_custom_range(self):
        """Test numeric parameter with custom min/max values."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal

        registry = EffectsRegistry()

        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/param2")
        graph.add((port_node, LV2.minimum, Literal(0.0)))
        graph.add((port_node, LV2.maximum, Literal(100.0)))
        graph.add((port_node, LV2.default, Literal(50.0)))

        result = registry._create_parameter_from_port(graph, port_node, "volume")

        assert result.min == 0.0
        assert result.max == 100.0
        assert result.default == 50.0

    def test_filename_parameter(self):
        """Test filename parameter for Path/String range type."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDFS

        registry = EffectsRegistry()

        graph = Graph()
        port_node = URIRef("http://test/param3")
        graph.add((port_node, RDFS.range, Literal("http://lv2plug.in/ns/lv2core#Path")))

        result = registry._create_parameter_from_port(graph, port_node, "model")

        assert result.name == "model"
        assert result.type == "filename"


class TestParseParameterSubject:
    """Tests for _parse_parameter_subject method."""

    def test_parse_numeric_parameter(self):
        """Test parsing a numeric parameter subject."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal

        registry = EffectsRegistry()

        graph = Graph()
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

        param_subject = URIRef("http://test/param1")
        graph.add((param_subject, RDFS.label, Literal("Gain")))

        result = registry._parse_parameter_subject(graph, param_subject)

        assert result is not None
        assert result["name"] == "Gain"
        assert result["parameter"].type == "number"

    def test_parse_filename_parameter(self):
        """Test parsing a filename parameter subject."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal

        registry = EffectsRegistry()

        graph = Graph()
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

        param_subject = URIRef("http://test/param2")
        graph.add((param_subject, RDFS.label, Literal("Model")))
        graph.add((param_subject, RDFS.range, Literal("http://lv2plug.in/ns/lv2core#Path")))

        result = registry._parse_parameter_subject(graph, param_subject)

        assert result is not None
        assert result["name"] == "Model"
        assert result["parameter"].type == "filename"


class TestParsePluginManifest:
    """Tests for _parse_plugin_manifest method."""

    def test_returns_none_for_missing_manifest(self, tmp_path):
        """Test returns None when manifest.ttl doesn't exist."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(tmp_path))
        assert result is None

    def test_uses_uri_as_name_fallback(self, tmp_path):
        """Test uses URI as name when no name found in manifest."""
        from mod_api.effects.registry import EffectsRegistry
        import tempfile

        # Create a minimal manifest.ttl
        manifest_dir = tmp_path / "test.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"

        # Minimal LV2 manifest
        manifest_ttl.write_text('''
@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/MyPlugin>
    a lv2:Plugin .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert result.uri == "http://example.com/MyPlugin"
        assert result.name == "MyPlugin"

    def test_uses_lv2_name_as_fallback(self, tmp_path):
        """Test uses lv2:name when no doap:name found."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "lv2name.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "lv2name.ttl"

        # Manifest with lv2:name instead of doap:name (in plugin.ttl)
        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/PluginWithLv2Name>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/PluginWithLv2Name>
    lv2:name "Plugin With LV2 Name" .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert result.name == "Plugin With LV2 Name"

    def test_uses_rdfs_label_as_fallback(self, tmp_path):
        """Test uses rdfs:label when no doap:name or lv2:name found (in plugin.ttl)."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "rdfslabel.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "rdfslabel.ttl"

        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/PluginWithRdfsLabel>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://example.com/PluginWithRdfsLabel>
    rdfs:label "Plugin With RDFS Label" .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert result.name == "Plugin With RDFS Label"

    def test_parses_plugin_ttl_for_ports(self, tmp_path):
        """Test that plugin.ttl is parsed for port definitions."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal, BNode
        from rdflib.namespace import RDF

        manifest_dir = tmp_path / "withports.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "withports.ttl"

        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/PluginWithPorts>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/PluginWithPorts>
    lv2:port [
        lv2:symbol "input" ;
        a <http://lv2plug.in/ns/lv2core#AudioPort>,
          <http://lv2plug.in/ns/lv2core#InputPort>
    ] ;
    lv2:port [
        lv2:symbol "output" ;
        a <http://lv2plug.in/ns/lv2core#AudioPort>,
          <http://lv2plug.in/ns/lv2core#OutputPort>
    ] .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert len(result.ports) == 2
        port_names = {p.name for p in result.ports}
        assert "input" in port_names
        assert "output" in port_names


class TestScanLv2Path:
    """Tests for _scan_lv2_path method."""

    def test_scan_empty_lv2_path(self):
        """Test scan returns empty list when LV2_PATH not set or empty."""
        from mod_api.effects.registry import EffectsRegistry
        from unittest.mock import patch

        registry = EffectsRegistry()
        with patch.dict('os.environ', {'LV2_PATH': ''}):
            result = registry._scan_lv2_path()
            assert result == []

    def test_scan_nonexistent_path(self):
        """Test scan skips nonexistent paths."""
        from mod_api.effects.registry import EffectsRegistry
        from unittest.mock import patch, MagicMock

        registry = EffectsRegistry()
        with patch('os.path.exists', return_value=False):
            result = registry._scan_lv2_path()
            assert result == []


class TestParsePortNodeEdgeCases:
    """Tests for _parse_port_node edge cases."""

    def test_port_symbol_fallback_to_lv2_name(self):
        """Test port uses lv2:name when symbol not present."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        registry = EffectsRegistry()
        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/port1")
        graph.add((port_node, LV2.name, Literal("port_name")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#AudioPort")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#InputPort")))

        result = registry._parse_port_node(graph, port_node)
        assert result is not None
        assert result["name"] == "port_name"

    def test_port_returns_none_without_name(self):
        """Test port returns None when no name property found."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef
        from rdflib.namespace import RDF

        registry = EffectsRegistry()
        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/port1")
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#AudioPort")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#InputPort")))

        result = registry._parse_port_node(graph, port_node)
        assert result is None

    def test_atom_port_not_parsed_as_parameter(self):
        """Test that AtomPort is not parsed as a control parameter."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        registry = EffectsRegistry()
        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        port_node = URIRef("http://test/atompot")
        graph.add((port_node, LV2.symbol, Literal("atom_port")))
        graph.add((port_node, RDF.type, URIRef("http://lv2plug.in/ns/lv2core#AtomPort")))

        result = registry._parse_port_node(graph, port_node)
        # AtomPort without ControlPort should not be parsed
        assert result is None


class TestParseParameterSubjectEdgeCases:
    """Tests for _parse_parameter_subject edge cases."""

    def test_symbol_used_when_label_missing(self):
        """Test symbol is used when rdfs:label is missing."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal

        registry = EffectsRegistry()
        graph = Graph()
        LV2 = Namespace("http://lv2plug.in/ns/lv2core#")

        param_subject = URIRef("http://test/param1")
        graph.add((param_subject, LV2.symbol, Literal("param_symbol")))

        result = registry._parse_parameter_subject(graph, param_subject)
        assert result is not None
        assert result["name"] == "param_symbol"

    def test_returns_none_without_name_properties(self):
        """Test returns None when no label or symbol present."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, URIRef

        registry = EffectsRegistry()
        graph = Graph()

        param_subject = URIRef("http://test/param1")

        result = registry._parse_parameter_subject(graph, param_subject)
        assert result is None

    def test_string_range_is_numeric(self):
        """Test that String range is treated as numeric parameter (not filename)."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal

        registry = EffectsRegistry()
        graph = Graph()
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

        param_subject = URIRef("http://test/param2")
        graph.add((param_subject, RDFS.label, Literal("StringParam")))
        graph.add((param_subject, RDFS.range, Literal("http://lv2plug.in/ns/lv2core#String")))

        result = registry._parse_parameter_subject(graph, param_subject)
        assert result is not None
        assert result["parameter"].type == "number"  # String range defaults to numeric


class TestDiscoverIntegration:
    """Tests for discover with actual filesystem scanning."""

    def test_discover_processes_found_plugins(self, tmp_path):
        """Test discover processes plugins found on the filesystem."""
        from mod_api.effects.registry import EffectsRegistry, EffectInfo
        from mod_api.models import Port

        registry = EffectsRegistry()

        # Create a mock plugin directory
        plugin_dir = tmp_path / "test_plugin.lv2"
        plugin_dir.mkdir()
        manifest_ttl = plugin_dir / "manifest.ttl"
        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/test_plugin>
    a lv2:Plugin .
''')

        with patch('mod_api.effects.registry.EffectsRegistry._scan_lv2_path', return_value=[str(plugin_dir)]):
            registry.discover()

        assert "http://example.com/test_plugin" in registry._effects

    def test_discover_handles_null_parse_result(self, tmp_path):
        """Test discover handles None results from parsing."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()

        with patch('mod_api.effects.registry.EffectsRegistry._scan_lv2_path', return_value=['nonexistent_path']):
            with patch.object(registry, '_parse_plugin_manifest', return_value=None):
                result = registry.discover()

        assert result == []


class TestRegistryFallbackUri:
    """Tests for fallback URI detection in manifest parsing."""

    def test_fallback_uri_detection_with_hash_in_uri(self, tmp_path):
        """Test fallback detects URI with hash fragment."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        manifest_dir = tmp_path / "hash_uri.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"

        # Create graph directly to test fallback logic
        manifest_ttl.write_text('''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
<http://example.com/#MyPlugin>
    a <http://lv2plug.in/ns/lv2core#Plugin> .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None

    def test_returns_none_without_any_plugin_uri(self, tmp_path):
        """Test returns None when no LV2.Plugin and no fallback URIs found."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "no_uri.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"

        # No LV2.Plugin declaration, no URI-like subjects - just a plain statement
        manifest_ttl.write_text('''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<urn:simple> .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is None


class TestPluginTtlParsing:
    """Tests for plugin.ttl name parsing with DOAP, LV2 name, and RDFS label."""

    def test_doap_name_in_plugin_ttl(self, tmp_path):
        """Test that doap:name in plugin.ttl is used for name."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "doapname.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "doapname.ttl"

        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/DoapPlugin>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix doap: <http://usefulinc.com/ns/doap#> .

<http://example.com/DoapPlugin>
    doap:name "DOAP Plugin Name" .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert result.name == "DOAP Plugin Name"

    def test_parameters_from_lv2_parameter_subject(self, tmp_path):
        """Test parsing standalone LV2.Parameter subjects."""
        from mod_api.effects.registry import EffectsRegistry
        from rdflib import Graph, Namespace, URIRef, Literal
        from rdflib.namespace import RDF

        manifest_dir = tmp_path / "lv2param.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "lv2param.ttl"

        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/ParamPlugin>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://example.com/ModelParam>
    a lv2:Parameter ;
    rdfs:label "model" ;
    rdfs:range <http://lv2plug.in/ns/lv2core#Path> .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert "model" in result.parameters
        assert result.parameters["model"].type == "filename"

    def test_parameter_from_lv2_port(self, tmp_path):
        """Test parameter extracted from lv2:port in plugin.ttl."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "paramport.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"
        plugin_ttl = manifest_dir / "paramport.ttl"

        manifest_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/ParamPortPlugin>
    a lv2:Plugin .
''')

        plugin_ttl.write_text('''@prefix lv2: <http://lv2plug.in/ns/lv2core#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://example.com/ParamPortPlugin>
    lv2:port [
        lv2:symbol "gain" ;
        a <http://lv2plug.in/ns/lv2core#ControlPort>
    ] .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None
        assert "gain" in result.parameters
        assert result.parameters["gain"].type == "number"

    def test_scan_skips_non_directory_entries(self, tmp_path):
        """Test scan skips files (not directories) in LV2 path."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()

        # Return a file alongside directories
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['file.lv2', 'other.lv2']):
                with patch('os.path.isdir', return_value=False):
                    result = registry._scan_lv2_path()

        assert result == []

    def test_scan_skips_directory_without_manifest(self, tmp_path):
        """Test scan skips directories without manifest.ttl."""
        from mod_api.effects.registry import EffectsRegistry

        registry = EffectsRegistry()

        def exists_side_effect(path):
            # Only /usr/lib/lv2 style paths exist, but manifest check fails
            if 'manifest.ttl' in path:
                return False
            return True

        with patch('os.path.exists', side_effect=exists_side_effect):
            with patch('os.path.isdir', return_value=True):
                with patch('os.listdir', return_value=['no_manifest.lv2']):
                    result = registry._scan_lv2_path()

        assert result == []


class TestFallbackUriDetection:
    """Tests for fallback URI detection when no LV2.Plugin found."""

    def test_fallback_uri_detection_with_slash_in_uri(self, tmp_path):
        """Test fallback detects URI with slash."""
        from mod_api.effects.registry import EffectsRegistry

        manifest_dir = tmp_path / "slash_uri.lv2"
        manifest_dir.mkdir()
        manifest_ttl = manifest_dir / "manifest.ttl"

        # URI without LV2.Plugin type but with slash
        manifest_ttl.write_text('''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
<http://example.com/SomePlugin>
    a <http://example.com#SomeClass> .
''')

        registry = EffectsRegistry()
        result = registry._parse_plugin_manifest(str(manifest_dir))

        assert result is not None