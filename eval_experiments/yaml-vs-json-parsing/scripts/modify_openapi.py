
import yaml

# Load the OpenAPI specification
with open('/home/yusuke/workspace/agentic-bootstrap/eval_experiments/yaml-vs-json-parsing/scenario-yaml/openapi.yaml', 'r') as f:
    content = f.read()

# Fix the malformed YAML
broken_part = """      properties:
          maxLength: 32"""
fixed_part = """      properties:
        username:
          maxLength: 32"""

content = content.replace(broken_part, fixed_part)

spec = yaml.safe_load(content)

# 1. Change the summary of the POST /orders endpoint
spec['paths']['/orders']['post']['summary'] = "Submit a new customer order."

# 2. Change the type of the quantity field in the OrderItem schema
spec['components']['schemas']['OrderItem']['properties']['quantity']['type'] = 'number'
spec['components']['schemas']['OrderItem']['properties']['quantity']['minimum'] = 0.1

# 3. Remove the deprecated: true flag from the GET /products/legacy endpoint
if 'deprecated' in spec['paths']['/products/legacy']['get']:
    del spec['paths']['/products/legacy']['get']['deprecated']

# 4. Change the status field enum values in the Order schema
spec['components']['schemas']['Order']['properties']['status']['enum'] = ["pending", "confirmed", "in_transit", "fulfilled", "cancelled"]

# 5. Add a x-internal: true extension to the DELETE /users/{userId} endpoint
spec['paths']['/users/{userId}']['delete']['x-internal'] = True

# Write the modified spec to the output file
with open('/home/yusuke/workspace/agentic-bootstrap/eval_experiments/yaml-vs-json-parsing/eval_results/gemini-2.5-pro/eval-2-yaml/output.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Modified OpenAPI spec written to output.yaml")
