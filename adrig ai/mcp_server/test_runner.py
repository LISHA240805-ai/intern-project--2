from mcp_server import registry
from mcp_server.engine import execute

print('Loaded tools:', list(registry.get_registry().keys()))
print('Describe get_flights:', registry.get_registry().get('get_flights'))
print('Execute local_echo:', execute('local_echo', {'message': 'hello world'}))
