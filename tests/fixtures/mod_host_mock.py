"""Mock mod-host TCP server for integration testing without Docker.

This provides a simple TCP server that mimics mod-host protocol responses,
simulating the behavior of a real mod-host server with JACK audio via /dev/snd.

/dev/snd Device Mocking:
- The enumerate command returns system:capture_1/2 and system:playback_1/2 ports
  to simulate the audio devices that would be available via /dev/snd in a real
  environment
- Effect instance ports (effect_N:input/output) are dynamically added when plugins
  are instantiated via the add command, simulating the JACK ports created by LV2 plugins

This mock is used by the integration test suite to test the Pedalboard API without
requiring:
- Docker or the mod-host container
- Real /dev/snd audio devices
- JACK audio server with real hardware
"""

import socket
import threading
import time

import pytest


class MockModHostServer:
    """A minimal TCP server that responds to mod-host protocol commands."""

    def __init__(self, host: str = "localhost", port: int = 5555):
        self.host = host
        self.port = port
        self.server_socket: socket.socket | None = None
        self.running = False
        self.thread: threading.Thread | None = None
        self.effect_instances: set[int] = set()
        # Store patch values for simulating property persistence
        self._patch_values: dict[tuple[int, str], str] = {}

    def start(self):
        """Start the mock server in a background thread."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=False)
        self.thread.start()
        # Wait for server to be ready and accept connections
        time.sleep(0.5)

    def stop(self):
        """Stop the mock server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    def _run(self):
        """Handle incoming connections."""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    conn, _ = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    # Socket closed
                    break

                conn.settimeout(5.0)
                while self.running:
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break
                        cmd = data.decode().strip()
                        response = self._handle_command(cmd)
                        conn.sendall((response + "\n").encode())
                    except socket.timeout:
                        # Keep connection alive, wait for more data
                        continue
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    except Exception:
                        break
                try:
                    conn.close()
                except Exception:
                    pass
            except Exception:
                break

    def _handle_command(self, cmd: str) -> str:
        """Process a mod-host command and return a response."""
        parts = cmd.split()
        if not parts:
            return "resp -902"  # ERR_INVALID_OPERATION

        command = parts[0]

        if command == "enumerate":
            # Return system ports (simulating /dev/snd devices)
            # In real mod-host, enumerate returns all loaded plugins and their ports
            ports = ["system:capture_1", "system:capture_2", "system:playback_1", "system:playback_2"]
            # Include effect instance ports for loaded plugins (simulating JACK ports created by LV2 plugins)
            for instance_id in sorted(self.effect_instances):
                ports.extend([f"effect_{instance_id}:input", f"effect_{instance_id}:output"])
            return "resp 0 " + " ".join(ports)
        elif command == "add":
            # add "uri" instance
            if len(parts) >= 3 and parts[-2].startswith('"'):
                instance_id = int(parts[-1])
                self.effect_instances.add(instance_id)
                return "resp 0"
            return "resp -102"  # ERR_LV2_INSTANTIATION
        elif command.startswith("remove"):
            instance_id = int(parts[1])
            self.effect_instances.discard(instance_id)
            return "resp 0"
        elif command == "patch_set":
            # patch_set <instance> <property_uri> <value>
            # Store the value for retrieval via patch_get (simulating property persistence)
            if len(parts) >= 4:
                instance_id = int(parts[1])
                property_uri = parts[2]
                value = parts[3] if len(parts) >= 4 else ""
                self._patch_values[(instance_id, property_uri)] = value
            return "resp 0"
        elif command.startswith("patch_get"):
            # patch_get <instance> <property_uri>
            # Return stored value or default
            try:
                instance_id = int(parts[1])
                property_uri = parts[2]
                value = self._patch_values.get((instance_id, property_uri), "")
                return f"resp 0 {value}"
            except (IndexError, ValueError):
                return "resp 0 "
        elif command == "connect":
            return "resp 0"
        elif command.startswith("disconnect"):
            return "resp 0"
        elif command.startswith("param_set"):
            return "resp 0"
        elif command.startswith("param_get"):
            return "resp 0 0.5"
        elif command == "cpu_load":
            return "resp 0 0.1"
        elif command == "bypass":
            return "resp 0"
        else:
            return "resp 0"


@pytest.fixture(scope="session")
def mod_host_mock():
    """Start a mock mod-host server for integration testing.

    Provides a TCP server on an available port that responds to mod-host protocol
    commands, simulating a real mod-host environment with /dev/snd audio devices.

    Returns a dict with:
    - control_port: The TCP port for mod-host control socket
    - feedback_port: The feedback port number (unused in mock, but kept for API compatibility)
    """
    # Try to find an available port
    for port in [5555, 5557, 5559, 5561]:
        server = MockModHostServer(port=port)
        try:
            server.start()
            break
        except OSError:
            # Port in use, try next
            continue
    else:
        raise RuntimeError("Could not find available port for mock mod-host server")

    yield {"control_port": port, "feedback_port": 5556}
    server.stop()
    # Small delay to ensure port is released
    time.sleep(0.1)